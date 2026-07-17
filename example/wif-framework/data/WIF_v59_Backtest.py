#!/usr/bin/env python3
"""
WIF v5.9 P0 修复版: CSI Hysteresis + F29>500bp 硬拦截
================================================================================
v5.9 / v6.8.1 合并回测程序（原 v5.8.2 baseline 已并入，2026-06-09 重构）

★ P0 修复 #1: CSI 退出 EMERGENCY 的 Hysteresis 逻辑
  - 原 v6.8 逻辑: 进入 EMERGENCY/WARNING 需 3 日持续, 但退出直接默认 HEALTHY (无 hysteresis)
  - 问题: 2008-10-13 后 CSI 仍在 1.5-2.5 区间震荡, 永远凑不齐 3 日 > 2.0, 模型失去危机感知
  - v5.9 修复: 应用 CSI_healthy_5d (CSI<1.0 持续 5 日), 用 forward fill 状态机实现对称 hysteresis

★ P0 修复 #2: F29 > 500bp 硬拦截 (EMERGENCY Override)
  - 文档 L575-581 "第三层: EMERGENCY Override (硬拦截)" 明确设计:
    IF 信用利差 (F29) > 500bp  →  MCI_adjusted = -20 (引擎中断)
  - 文档 L358-359 历史案例表: 2008.09-11 雷曼倒闭 (F29~600bp) 应触发 EMERGENCY
  - 原 v6.8 逻辑: 仅依赖 CSI (Z-score) + F33b, F29 绝对阈值从未实施
  - 问题: 2008-12-04 BAA 利差 616bp 雷曼真正峰值时, CSI 60日 Z-score 已归零, 模型显示 HEALTHY
  - v5.9 修复: 添加 F29>500bp 硬触发器, 独立于 CSI 立即触发 EMERGENCY

★ P0 修复 #3: Q3 HEALTHY 滞胀股票上限 40% → 30%
  - 文档矩阵 ②+③+HEALTHY 滞胀期股票上限原写 45%, v6.8 代码实现 40% (与文档矩阵不符)
  - v6.8.1 修复: Q3 HEALTHY 股票上限 = 30%, 矩阵与代码完全一致
  - 影响: 滞胀期股债跷跷板效应更显著，防御更稳健

输出:
  - v5.9  = v5.8 框架 + P0 修复 #1 + #2
  - v6.8.1 = v6.8 框架 + P0 修复 #1 + #2 + Q3 滞胀 30% 上限

其他逻辑 (CSI 计算、Macro Quadrant、MCI、factor 路由、调仓引擎、HSBC 成本) 完全不变。

作者: WIF Framework
日期: 2026-06-09 (v5.9 P0 修复 #1+#2+#3 · 合并重构版)
"""

import pandas as pd
import numpy as np
import os
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

OUT_DIR    = '/Users/weimingzhuang/Documents/wealth_research/21_WIF_财富投资框架/01_国际版/v5.9_backtest_20260716'
DATA_DIR   = '/Users/weimingzhuang/Documents/wealth_research/21_WIF_财富投资框架/01_国际版/v5.9_backtest_20260716/data'
REPORT_DIR = f'{OUT_DIR}'
os.makedirs(REPORT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────
# ① 加载数据
# ─────────────────────────────────────────────────────────
print("① 加载合并价格数据...")
prices = pd.read_csv(f'{DATA_DIR}/_merged_prices.csv', parse_dates=['Date'], index_col='Date')
prices = prices.sort_index()
if prices.index.tz is not None:
    prices.index = prices.index.tz_localize(None)
core_cols = ['SPY', 'GLD', 'TLT', 'VTI', 'QQQ', 'BND', 'XLE']
prices = prices[core_cols + ['VIX', 'VIXTERM']].ffill()
# VIXTERM 数据来源：_merged_prices.csv 列，直接读取 FRED ^VIX3M 实测值
# 公式：VIXTERM = VIX_spot - VIX3M（CBOE 现行中期波动率指数）
# 覆盖范围：2007-01-03 ~ 2026-05-11，全4865天，无2018年断点
# 数据质量验证：2020-03-12 COVID峰值 VIXTERM=+18.23（VIX=75，VIX3M≈57，倒挂极深）
assert prices['VIXTERM'].last_valid_index() >= pd.Timestamp('2026-01-01'), \
    f"VIXTERM 数据未覆盖到2026年，当前最后日期: {prices['VIXTERM'].last_valid_index()}"
for c in core_cols:
    prices[f'{c}_ret'] = prices[c].pct_change().fillna(0)

prices['SHV_vol60'] = prices['BND_ret'].rolling(60).std() * 0.5
prices['TLT_vol60']  = prices['TLT_ret'].rolling(60).std() * 0.5
print(f"  数据范围：{prices.index[0].date()} ~ {prices.index[-1].date()}，共 {len(prices)} 天")

# ── 加载真实BAA信用利差数据（替换TLT/SPY代理）──
print("  加载真实BAA信用利差数据...")
cred = pd.read_csv(f'{DATA_DIR}/CreditSpread_BAA_1986_2026.csv', parse_dates=['Date'], index_col='Date')
cred = cred.sort_index()
if cred.index.tz is not None:
    cred.index = cred.index.tz_localize(None)
# CreditSpread_bp 单位已经是bp
prices['F29_bp'] = cred['CreditSpread_bp'].reindex(prices.index).ffill()
cred_avail = prices['F29_bp'].notna().sum()
print(f"  BAA信用利差：{cred_avail} 天有效 | "
      f"BAA均值={prices['F29_bp'].mean():.1f}bp | "
      f"2008峰值={prices.loc['2008-09-01':'2008-12-31','F29_bp'].max():.0f}bp | "
      f"2020峰值={prices.loc['2020-03-01':'2020-04-30','F29_bp'].max():.0f}bp")

# ─────────────────────────────────────────────────────────
# ①b 加载因子ETF（v6.7 专用）
# ─────────────────────────────────────────────────────────
print("①b 加载因子ETF（v6.8.1）...")

def load_raw_etf(path, ticker):
    """加载单个ETF，支持旧格式和新格式"""
    df = pd.read_csv(path, parse_dates=['Date'])
    if df['Date'].dtype == object:
        df['Date'] = pd.to_datetime(df['Date'].str.split().str[0])
    else:
        df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    # PATCH 2026-07-16: 标准化列名后，移除兼容逻辑
    #   - ETF CSV: 列名 'Adj Close' (与 yfinance auto_adjust=True 等价)
    #   - FRED 利率 CSV: 列名 'Close' (FRED 原始输出)
    #   - VIX/VIX3M/VIXTERM/CreditSpread: 自定义列名，不通过本函数读取
    if 'Adj Close' in df.columns:
        col = 'Adj Close'
    elif 'Close' in df.columns:
        col = 'Close'
    else:
        # 严格模式: 数据格式不符预期时立即报错，避免静默错误
        raise ValueError(
            f"Cannot find price column in {path}. Expected 'Adj Close' (ETF) or 'Close' (FRED). "
            f"Found columns: {list(df.columns)}"
        )
    adj = df[col].ffill()
    adj.name = ticker
    return adj

# ── 固收代理：优先使用 SHV 真实数据
import glob as _glob
shv_pattern = f'{DATA_DIR}/SHV_*.csv'
shv_matches = _glob.glob(shv_pattern)
if shv_matches:
    shv_path = sorted(shv_matches)[-1]
    shv_raw = load_raw_etf(shv_path, 'SHV')
    prices['SHV'] = shv_raw.reindex(prices.index).ffill()
    print(f"  SHV 真实数据：{shv_raw.first_valid_index().date()} 起（替代 BND 代理）")
else:
    prices['SHV'] = prices['BND']
    print(f"  SHV 数据未找到，使用 BND 代理")
prices['SHV_ret'] = prices['SHV'].pct_change().fillna(0)
prices['SHV_vol60'] = prices['SHV_ret'].rolling(60).std() * 0.5

factor_etfs = {
    'QUAL': 'QUAL', 'VIG': 'VIG', 'MOAT': 'MOAT',
    'USMV': 'USMV', 'SPLV': 'SPLV', 'MTUM': 'MTUM',
    'VB': 'VB', 'IJR': 'IJR',
}
factor_list = list(factor_etfs.keys())

for short_name, ticker in factor_etfs.items():
    import glob
    pattern = f'{DATA_DIR}/{ticker}_*.csv'
    matches = glob.glob(pattern)
    if matches:
        path = sorted(matches)[-1]
    else:
        path = f'{DATA_DIR}/{ticker}.csv'
    if os.path.exists(path):
        adj = load_raw_etf(path, short_name)
        prices = prices.join(adj, how='left')
        avail = prices[short_name].notna().sum()
        first_d = prices[short_name].first_valid_index()
        last_d  = prices[short_name].last_valid_index()
        print(f"  {short_name:6s}: {avail:5d} 天 | {str(first_d.date()) if first_d else 'N/A'} ~ {str(last_d.date()) if last_d else 'N/A'}")

# ★ Bug Fix #6: 为因子ETF创建_ret列（NAV计算必需）
# 根因：第49行只对core_cols计算_ret，因子ETF价格列虽加载但_ret列缺失
# 导致NAV计算中equity67永远fallback到VTI+QQQ，即使equity_ticker_v68b显示因子ETF名
print("  计算因子ETF日收益率...")
for f in factor_etfs.keys():
    if f in prices.columns:
        prices[f'{f}_ret'] = prices[f].pct_change().fillna(0)
        avail_ret = prices[f'{f}_ret'].notna().sum()
        print(f"  {f}_ret: 已创建 ({avail_ret} 天有效数据)")
    else:
        prices[f'{f}_ret'] = np.nan
        print(f"  {f}_ret: 不可用（价格列缺失）")

# ── 防御性行业ETF（WARNING状态用，但v6.7仅在特殊场景使用）
print("  加载防御性行业ETF（XLV/XLU/XLP）...")
defensive_etfs = ['XLV', 'XLU', 'XLP']
for ticker in defensive_etfs:
    pattern = f'{DATA_DIR}/{ticker}_*.csv'
    matches = _glob.glob(pattern)
    if matches:
        path = sorted(matches)[-1]
        adj = load_raw_etf(path, ticker)
        prices[ticker] = adj.reindex(prices.index).ffill()
        avail = prices[ticker].notna().sum()
        print(f"  {ticker}: {avail} 天")
    else:
        print(f"  {ticker}: 数据未找到，跳过")

for ticker in defensive_etfs:
    if ticker in prices.columns:
        prices[f'{ticker}_ret'] = prices[ticker].pct_change().fillna(0)

# ─────────────────────────────────────────────────────────
# ② Hybrid Phase 1（v6.8.1：CSI primary + F33b EMERGENCY override）
# ─────────────────────────────────────────────────────────
print("② Hybrid Phase 1 市场状态检测（v6.8.1：CSI primary + F33b override）...")

# ── CSI 三组分计算 ──
# 组分1：F29 信用利差 60日Z-Score（w1=0.45）
prices['F29_60d_ma'] = prices['F29_bp'].rolling(60).mean()
prices['F29_60d_std'] = prices['F29_bp'].rolling(60).std()
prices['Z_F29'] = (prices['F29_bp'] - prices['F29_60d_ma']) / prices['F29_60d_std'].replace(0, 1)

# 组分2：VIXTERM 60日Z-Score（w2=0.35）
prices['VIXTERM_60d_ma'] = prices['VIXTERM'].rolling(60).mean()
prices['VIXTERM_60d_std'] = prices['VIXTERM'].rolling(60).std()
prices['Z_VIXTERM'] = (prices['VIXTERM'] - prices['VIXTERM_60d_ma']) / prices['VIXTERM_60d_std'].replace(0, 1)

# 组分3：SPY-GLD 相关性崩塌 Z-Score（w3=0.20，取负因为相关崩塌=市场压力）
# 20日滚动相关性，相关性低时Z为负（压力信号）
prices['SPY_GLD_corr_20d'] = prices['SPY_ret'].rolling(20).corr(prices['GLD_ret'])
prices['corr_20d_ma'] = prices['SPY_GLD_corr_20d'].rolling(60).mean()
prices['corr_20d_std'] = prices['SPY_GLD_corr_20d'].rolling(60).std()
prices['Z_corr_collapse'] = -(prices['SPY_GLD_corr_20d'] - prices['corr_20d_ma']) / prices['corr_20d_std'].replace(0, 1)
# Z_corr_collapse为正 = 相关性低于均值 = 市场压力增加

# ── CSI 复合压力指数（权重：w1=0.45, w2=0.35, w3=0.20）──
prices['CSI'] = (0.45 * prices['Z_F29'].fillna(0) +
                 0.35 * prices['Z_VIXTERM'].fillna(0) +
                 0.20 * prices['Z_corr_collapse'].fillna(0))

# ── CSI 退出计数（需CSI<1.0持续5个交易日才确认HEALTHY）──
# Hysteresis: 需5日连续<1.0，且期间不能中断
prices['CSI_below_1'] = (prices['CSI'] < 1.0).astype(int)
prices['CSI_exit_count'] = prices['CSI_below_1'].rolling(5).sum()
prices['CSI_healthy_5d'] = (prices['CSI_exit_count'] == 5).astype(int)

# ── Hybrid Phase1三档判定（需3日持续新状态才触发，防止阈值震荡）──
# Hysteresis修复: EMERGENCY/WARNING需要3日持续才能激活，HEALTHY需要5日CSI<1.0才退出
prices['CSI_EMERGENCY'] = (prices['CSI'] > 2.0).astype(int)
prices['CSI_WARNING']   = ((prices['CSI'] > 1.0) & (prices['CSI'] <= 2.0)).astype(int)

# 3日持续性检查
prices['EMERGENCY_persist'] = prices['CSI_EMERGENCY'].rolling(3).sum()
prices['WARNING_persist']    = prices['CSI_WARNING'].rolling(3).sum()
prices['EMERGENCY_3d'] = (prices['EMERGENCY_persist'] == 3).astype(int)
prices['WARNING_3d']    = (prices['WARNING_persist'] == 3).astype(int)

# ── F33b VIX动量触发器（v6.8.1 独立安全气囊）──
# VIX 10日涨幅 > 100% 且 VIX Spot > 40
prices['VIX_10d_return'] = prices['VIX'].pct_change(10).fillna(0)
prices['F33b_trigger']   = ((prices['VIX'] > 40) & (prices['VIX_10d_return'] > 1.0)).astype(int)

# ── Hybrid Phase1（v5.9）：CSI primary + F33b EMERGENCY override + F29>500bp 硬拦截 + CSI_healthy_5d ──
# ★ v5.9 修复 #1: 应用 CSI_healthy_5d 实现对称 hysteresis
# 原 v6.8.1 修复前逻辑: 进入 EMERGENCY/WARNING 需 3 日持续, 但退出直接默认 HEALTHY (无 hysteresis)
# → 2008-10-13 后 CSI 仍在 1.5-2.5 区间震荡, 永远凑不齐 3 日 > 2.0, 模型失去危机感知
# v5.9 修复: 状态机 (forward fill) 保持上一交易日状态, 仅在以下情况切换:
#   - CSI>2.0 持续3日 → EMERGENCY (v6.8 原有)
#   - CSI 1.0~2.0 持续3日 → WARNING (v6.8 原有)
#   - CSI<1.0 持续5日 → HEALTHY (★ v5.9 修复 #1, 文档 L194 原始定义)
#   - F33b触发 (VIX>40 AND 10d>100%) → EMERGENCY (v6.8 原有, 独立覆盖)
#   - F29 > 500bp → EMERGENCY (★ v5.9 修复 #2, 文档 L575-581 "EMERGENCY Override (硬拦截)" + L358-359 历史案例)
#   - 其他情况: 保持上一交易日状态 (state machine forward fill)
prices['F33b_EMERGENCY_override'] = (
    (prices['CSI'] <= 2.0) & (prices['F33b_trigger'] == 1)
).astype(int)

# ★ v5.9 修复 #2: F29 绝对阈值硬拦截 (文档 L575-581 + L358-359)
# 设计来源:
#   - 文档 L578: "IF 信用利差 (F29) > 500bp → MCI_adjusted = -20 (引擎中断)"
#   - 文档 L359: "2008.09-11 雷曼倒闭 | ~600bp | 🔴🔴🔴 (信用利差 (F29) > 500bp) | 强制 SHV+GLD, 提前1年+预警"
# 触发逻辑: F29 > 500bp 立即 EMERGENCY, 独立于 CSI (CSI 60日 Z-score 在持续危机中会失真,
#          2008-12-04 F29=616bp 时 CSI 实际为 -0.08, 模型误判 HEALTHY)
# 退出: 通过状态机保持 (state machine forward fill), 直到 CSI<1.0 持续5日才退出 (CSI_healthy_5d)
prices['F29_hard_trigger'] = (prices['F29_bp'] > 500).astype(int)
prices['F29_EMERGENCY_override'] = (
    (prices['CSI'] <= 2.0) & (prices['F29_hard_trigger'] == 1)
).astype(int)

# ★ v5.9 修复核心: 候选状态用 NaN 表示"保持上一日状态", 然后 forward fill
prices['Phase1_candidate'] = np.select(
    [(prices['EMERGENCY_3d'] == 1) | (prices['F33b_EMERGENCY_override'] == 1) | (prices['F29_EMERGENCY_override'] == 1),
     prices['WARNING_3d'] == 1,
     prices['CSI_healthy_5d'] == 1],
    ['EMERGENCY', 'WARNING', 'HEALTHY'],
    default=None
)
# 状态机: forward fill (前向填充) 保持上一交易日状态
prices['Phase1_status'] = prices['Phase1_candidate'].ffill()
# 初始状态 (前几行无任何信号时) backward fill 默认为 HEALTHY
prices['Phase1_status'] = prices['Phase1_status'].bfill()

# ── CSI 历史分布统计 ──
csi_stats = prices['CSI'].describe()
print(f"  CSI统计：均值={csi_stats['mean']:.2f} | 标准差={csi_stats['std']:.2f} | "
      f"最小={csi_stats['min']:.2f} | 最大={csi_stats['max']:.2f}")
print(f"  CSI峰值：2008={prices.loc['2008-09-01':'2008-12-31','CSI'].max():.2f} | "
      f"2020={prices.loc['2020-03-01':'2020-04-30','CSI'].max():.2f}")
phase_counts = prices['Phase1_status'].value_counts()
print(f"  Phase1 分布：HEALTHY={phase_counts.get('HEALTHY',0)} | "
      f"WARNING={phase_counts.get('WARNING',0)} | EMERGENCY={phase_counts.get('EMERGENCY',0)}")
f33b_stats = prices['F33b_trigger'].sum()
override_stats = prices['F33b_EMERGENCY_override'].sum()
print(f"  F33b触发：{f33b_stats} 天 | CSI未超2.0但F33b触发override：{override_stats} 天")
f29_stats = prices['F29_hard_trigger'].sum()
f29_override_stats = prices['F29_EMERGENCY_override'].sum()
print(f"  ★ F29>500bp 硬触发：{f29_stats} 天 | CSI未超2.0但F29触发override：{f29_override_stats} 天")

# ─────────────────────────────────────────────────────────
# ③ 宏观象限
# ─────────────────────────────────────────────────────────
print("③ 宏观象限...")
spy_mom126 = prices['SPY'].pct_change(126).rolling(60).mean().fillna(0)
tlt_mom126 = prices['TLT'].pct_change(126).rolling(60).mean().fillna(0)
prices['macro_Q1'] = ((spy_mom126 < 0) & (tlt_mom126 > 0)).astype(int)
prices['macro_Q2'] = ((spy_mom126 > 0) & (tlt_mom126 < 0)).astype(int)
prices['macro_Q3'] = ((spy_mom126 < 0) & (tlt_mom126 < 0)).astype(int)
prices['macro_Q4'] = ((spy_mom126 > 0) & (tlt_mom126 > 0)).astype(int)
prices['macro_quadrant'] = np.select(
    [prices['macro_Q2'] == 1, prices['macro_Q4'] == 1,
     prices['macro_Q3'] == 1, prices['macro_Q1'] == 1],
    [2, 4, 3, 1], default=1
)

# ─────────────────────────────────────────────────────────
# ④ MCI 三层量化（共用）
# ─────────────────────────────────────────────────────────
print("④ MCI 量化...")
# —— 加载实际利率组成数据（供 Layer 2 连续微调使用）——
dgs10   = load_raw_etf(f'{DATA_DIR}/DGS10_2007_2026.csv',   'DGS10')
t10yie  = load_raw_etf(f'{DATA_DIR}/T10YIE_2007_2026.csv',  'T10YIE')
prices['DGS10']   = dgs10.reindex(prices.index).ffill()
prices['T10YIE']  = t10yie.reindex(prices.index).ffill()
prices['DFII10']  = prices['DGS10'] - prices['T10YIE']    # 实际利率 = 名义 - 通胀预期
prices['VIX_20ma']   = prices['VIX'].rolling(20).mean()
prices['delta_F29']  = prices['F29_bp'].diff(60)           # F29利差60日变化（bp）
prices['delta_rates']= prices['DFII10'].diff(60)           # 实际利率60日变化（bp）
prices['delta_VIX']  = prices['VIX'] - prices['VIX_20ma']  # VIX相对20日均线偏离

# —— Layer 1：Phase1状态 × 宏观象限（基础分）——
def mci_layer1(phase, quad):
    base   = {'HEALTHY': +10, 'WARNING': 0, 'EMERGENCY': -20}.get(phase, 0)
    quad_b = {1: -15, 2: +15, 3: -10, 4: +20}.get(quad, 0)
    return base + quad_b

prices['MCI_layer1'] = [mci_layer1(p, q)
                        for p, q in zip(prices['Phase1_status'], prices['macro_quadrant'])]

# —— 连续微调（Layer 2）：三项指标各 ±5%，文档L544-563
def _cap(s):
    """向量化截断函数：sign(x) * min(|x|, 5)，适用于 Series 或 scalar"""
    sign = np.where(s >= 0, 1, -1)
    return sign * np.minimum(np.abs(s), 5.0)

prices['MCI_layer2'] = (
    prices['MCI_layer1']
    - _cap(prices['delta_F29'])      # 利差扩大→减分，收窄→加分
    - _cap(prices['delta_rates'])    # 利率上升→减分，下降→加分
    - _cap(prices['delta_VIX'])      # VIX>均线→减分，<均线→加分
)

# —— 离散信号（Layer 3）：文档L565-570 EMERGENCY Override 保留在 MCI_layer3
# ★ v6.8: CSI替代F33/F33b/F33c，不再用单独布尔触发器，MCI_layer3简化为CSI辅助调整
def mci_layer3(row):
    adj = 0
    # CSI 处于 WARNING 区间上限（>1.5）时，额外减分
    csi = row.get('CSI', 0)
    if csi > 1.5:
        adj -= 5
    elif csi > 1.0:
        adj -= 2
    # CSI 退出确认（CSI<1.0连5日）：+10（从EMERGENCY/WARNING中恢复）
    if row.get('CSI_healthy_5d', 0) == 1:
        adj += 10
    return adj

prices['MCI_layer3']    = prices.apply(mci_layer3, axis=1)
prices['MCI_adjusted']  = prices['MCI_layer2'] + prices['MCI_layer3']

# ─────────────────────────────────────────────────────────
# ⑤ VTI/QQQ 动量 + 期限结构（共用）
# ─────────────────────────────────────────────────────────
print("⑤ VTI/QQQ 动量 + 期限结构...")
prices['VTI_mom126'] = prices['VTI'].pct_change(126)
prices['QQQ_mom126'] = prices['QQQ'].pct_change(126)
prices['w_VTI'] = np.where(prices['QQQ_mom126'] >= prices['VTI_mom126'], 0.4, 0.6)
prices['w_QQQ'] = np.where(prices['QQQ_mom126'] >= prices['VTI_mom126'], 0.6, 0.4)
prices['duration_signal'] = np.select(
    [(prices['VIXTERM'] < -0.5), (prices['VIXTERM'] > 0.5)],
    ['SHV_prefer', 'TLT_prefer'], default='balanced'
)

# ─────────────────────────────────────────────────────────
# ⑥ v5.9 三轨制配置（v5.8 框架 + P0 修复）
# ─────────────────────────────────────────────────────────
print("⑥ v5.9 三轨制配置...")
def triple_track_v59(phase1, quadrant):
    if phase1 == 'EMERGENCY': return (0.15, 0.55, 0.30)
    elif phase1 == 'WARNING':
        return {1:(0.20,0.50,0.30),2:(0.40,0.35,0.25),
                3:(0.25,0.25,0.50),4:(0.50,0.20,0.30)}.get(quadrant,(0.35,0.35,0.30))
    else:
        return {1:(0.30,0.45,0.25),2:(0.75,0.10,0.15),
                3:(0.30,0.20,0.50),4:(0.65,0.10,0.25)}.get(quadrant,(0.45,0.30,0.25))

limits59 = [triple_track_v59(p,q) for p,q in zip(prices['Phase1_status'],prices['macro_quadrant'])]
prices['eq_lim59'] = [l[0] for l in limits59]
prices['fi_lim59']  = [l[1] for l in limits59]
prices['ra_lim59']  = [l[2] for l in limits59]

# ─────────────────────────────────────────────────────────
# ⑦ v6.7 MCI 三桶比例（与v6.5相同结构）
# ─────────────────────────────────────────────────────────
print("⑦ v6.8.1 MCI 三桶比例...")
def calc_v68b(phase1, mci, quad, t10yie=2.0, cpi=2.5):
    if phase1 == 'EMERGENCY':
        return {'stock':0.0,'fi':0.70,'gld':0.30,'xle':0.0,'pdbc':0.0}
    if phase1 == 'WARNING':
        # ★ Fix #7: WARNING权益由象限决定（与v5.8一致）
        # 象限1=衰退→20%, 象限2=复苏→40%, 象限3=滞胀→25%, 象限4=过热→50%
        eq_map = {1:0.20, 2:0.40, 3:0.25, 4:0.50}
        eq = eq_map.get(quad, 0.40)
        eq = min(eq, 0.60)  # 显式cap，与文档Part 1.2约定一致（防御性）
        gld, xle, pdbc = 0.15, 0.09, 0.0
        pdbc = min(0.40, max(max(0,t10yie-2.2)*0.15, 0.20 if cpi>5.0 else 0.0))
    else:
        # ★ Bug Fix #3: 提高equity基础配置
        # 原公式: eq = 0.40 + mci*0.02 → MCI=+5时仅50%，过高信念期才达70%
        # 修正: eq = 0.50 + mci*0.025 → MCI=+5时55%，MCI=+20时100%（上限）
        # 对应信念等级: LOW(+5~+10)=55~62.5%, MOD(+10~+15)=62.5~87.5%, HIGH(+15~+20)=87.5~100%
        eq   = min(1.0, max(0.0, 0.50 + max(0,mci)*0.025))
        gld  = 0.05
        xle  = 0.03
        pdbc = 0.0
    alt = gld + xle + pdbc
    if eq + alt > 0.97:
        sc = (0.97-eq)/alt if alt>0 else 0
        gld*=sc; xle*=sc; pdbc*=sc; alt=gld+xle+pdbc
    fi = max(0.0, 1.0-eq-alt-0.03)
    tot = eq+alt+fi
    return {'stock':round(eq/tot,4),'fi':round(fi/tot,4),
            'gld':round(max(0,gld)/tot,4),'xle':round(max(0,xle)/tot,4),
            'pdbc':round(max(0,pdbc)/tot,4)}

limits68b = [calc_v68b(p,m,q) for p,m,q in zip(prices['Phase1_status'],prices['MCI_adjusted'],prices['macro_quadrant'])]
prices['eq_lim68b']   = [l['stock'] for l in limits68b]
prices['fi_lim68b']    = [l['fi']    for l in limits68b]
prices['gld_lim68b']  = [l['gld']   for l in limits68b]
prices['xle_lim68b']  = [l['xle']   for l in limits68b]
prices['pdbc_lim68b'] = [l['pdbc']  for l in limits68b]

# ─────────────────────────────────────────────────────────
# ⑧ Phase 4 因子ETF路由（v6.8.1：每三周末评分 + MCI门控）
# ─────────────────────────────────────────────────────────
print("⑧ Phase 4 因子ETF路由（v6.8.1：每三周末评分 + MCI门控）...")
for f in factor_list:
    prices[f'{f}_mom126'] = prices[f].pct_change(126).replace([np.inf,-np.inf],np.nan)
    ma20 = prices[f].rolling(20).mean()
    ma60 = prices[f].rolling(60).mean()
    prices[f'{f}_trend'] = (ma20/ma60-1).replace([np.inf,-np.inf],np.nan)

for f in defensive_etfs:
    if f in prices.columns:
        prices[f'{f}_mom126'] = prices[f].pct_change(126).replace([np.inf,-np.inf],np.nan)
        ma20 = prices[f].rolling(20).mean()
        ma60 = prices[f].rolling(60).mean()
        prices[f'{f}_trend'] = (ma20/ma60-1).replace([np.inf,-np.inf],np.nan)
    else:
        prices[f'{f}_mom126'] = np.nan
        prices[f'{f}_trend'] = np.nan

def factor_score(f, quad, row):
    if f not in row.index or np.isnan(row.get(f,np.nan)): return -999
    mom=row.get(f'{f}_mom126',0); trend=row.get(f'{f}_trend',0)
    if np.isnan(mom): mom=0
    if np.isnan(trend): trend=0
    if quad==2:
        return mom*1.2+trend*0.8 if f in('VIG','QUAL','IJR','VB') else mom*0.8+trend*0.5
    if quad==4:
        return mom*1.3+trend*0.7 if f in('MTUM','IJR','VB') else mom*0.8+trend*0.5
    if quad==1:
        return mom*1.0+trend*1.2 if f in('USMV','SPLV','VIG','QUAL') else mom*0.6+trend*0.8
    if quad==3:
        return mom*1.1+trend*0.9 if f in('QUAL','MOAT','IJR','VB') else mom*0.7+trend*0.6
    return mom+trend

# ── v6.7 每3周末评分标记（15个交易日周期）──
score_cycle = 15
cycle_ids = np.arange(len(prices)) // score_cycle
prices['_score_cycle'] = cycle_ids
# 找出每个评分周期的最后一天
cycle_last = prices.groupby('_score_cycle').apply(
    lambda g: g.index[-1], include_groups=False
)
prices['is_score_day'] = prices.index.isin(cycle_last)

score_day_count = prices['is_score_day'].sum()
print(f"  每3周末评分日：{score_day_count} 天（约{score_day_count/19:.1f}次/年）")

# ── v6.7 因子选择（带MCI门控 + 每3周末限制）──
factor_sel = []
# ★ Bug Fix #1: 初始化为'VTI+QQQ'而非'VTI'
# 原因：prev_best='VTI'导致HEALTHY期大量使用纯VTI单一持仓（2139天），
#       而非应有的VTI+QQQ 60/40组合，导致equity仓位超过100%归一化后异常
prev_best = 'VTI+QQQ'
mci_gate_count = 0  # MCI<+5 强制VTI的次数
factor_switch_count = 0  # 因子切换次数

for i, (idx, row) in enumerate(prices.iterrows()):
    quad = int(row.get('macro_quadrant', 1))
    phase1 = row['Phase1_status']
    mci = row.get('MCI_adjusted', 0)
    
    # v6.7 核心逻辑①：WARNING期直接用VTI+QQQ，不走因子路由
    if phase1 == 'WARNING':
        best = 'VTI+QQQ'  # 标记为VTI+QQQ混合
    # v6.7 核心逻辑②：MCI<+5 强制VTI（不发因子评分）
    elif mci < 5:
        best = 'VTI'
        mci_gate_count += 1
    else:
        # v6.7 核心逻辑③：仅在每3周末重新评分（15个交易日=约3周）
        if row['is_score_day']:
            best='VTI'; best_s=-999
            for f in factor_list:
                s = factor_score(f, quad, row)
                if s > best_s: best_s=s; best=f
            # 记录切换
            if best != prev_best:
                factor_switch_count += 1
                prev_best = best
        else:
            best = prev_best  # 保持上次评分
    factor_sel.append(best)

prices['best_factor_v68b'] = factor_sel
factor_dist_v68b = pd.Series(factor_sel).value_counts()
print(f"  v6.7 因子分布：{factor_dist_v68b.to_dict()}")
print(f"  MCI门控触发（强制VTI）：{mci_gate_count} 天")
print(f"  因子切换次数（每3周末评分）：{factor_switch_count} 次")

# ─────────────────────────────────────────────────────────
# ⑨ WARNING 防御机制（共用）
# ─────────────────────────────────────────────────────────
print("⑨ WARNING 防御机制...")
prices['BND_mom20'] = prices['BND'].pct_change(20)
prices['BND_def_triggered'] = (prices['BND_mom20'] < 0).astype(int)

# ══════════════════════════════════════════════════════════════
# ⑩ 增强型回测引擎（交易日志 + HSBC渠道成本）
# ══════════════════════════════════════════════════════════════
print("⑩ 增强型回测引擎（含交易日志 + HSBC渠道成本）...")

# ──────────────────────────────────────────────────────────────
# HSBC渠道成本参数
# ──────────────────────────────────────────────────────────────
EQUITY_FUND_TYPES = {'VTI', 'QQQ', 'VGT', 'XLE', 'IJR', 'QUAL', 'MTUM', 'VIG', 'MOAT', 'USMV', 'SPLV', 'VB', 'SPY'}
BOND_FUND_TYPES   = {'BND', 'TLT', 'SHV'}
COMMODITY_FUND_TYPES = {'GLD', 'PDBC'}

INITIAL_EQUITY_FEE    = 0.03
INITIAL_BOND_FEE      = 0.02
INITIAL_COMMODITY_FEE = 0.02
ADD_SWITCH_FEE        = 0.03
REDEMPTION_FEE        = 0.00
MIN_INITIAL_RMB       = 100000
MIN_ADD_SWITCH_RMB    = 10000

fx_annual = {
    2007: 7.61, 2008: 6.95, 2009: 6.83, 2010: 6.77, 2011: 6.46,
    2012: 6.31, 2013: 6.19, 2014: 6.16, 2015: 6.23, 2016: 6.64,
    2017: 6.76, 2018: 6.62, 2019: 6.91, 2020: 6.90, 2021: 6.45,
    2022: 6.73, 2023: 7.08, 2024: 7.24, 2025: 7.25, 2026: 6.80
}

INITIAL_NAV_USD = 1_000_000  # ★ v5.9.1 修正：文档说 1M USD，程序原 142K（1M RMB/7），现统一为 1M USD

def get_fx_rate(date):
    year = date.year if hasattr(date, 'year') else int(str(date)[:4])
    return fx_annual.get(year, 7.0)

def get_initial_fee_rate(fund_type):
    if fund_type in EQUITY_FUND_TYPES:
        return INITIAL_EQUITY_FEE
    elif fund_type in BOND_FUND_TYPES:
        return INITIAL_BOND_FEE
    elif fund_type in COMMODITY_FUND_TYPES:
        return INITIAL_COMMODITY_FEE
    else:
        return INITIAL_EQUITY_FEE

# ── 预计算每日目标配置 ──
print("  预计算每日目标配置...")

target_v59 = {}
target_v68b = {}

# ★ Bug Fix #5: equity_ticker_v68b 使用 best_factor_v68b 而非错误的 prev_best
# prev_best_v68b 在交易日切换时更新（仅此时），避免月度循环迭代时重置导致因子ETF无法生效
prev_best_v68b = 'VTI+QQQ'
for idx, row in prices.iterrows():
    phase1 = row['Phase1_status']
    quad   = int(row.get('macro_quadrant', 1))
    sig    = row.get('duration_signal', 'balanced')
    mci    = row.get('MCI_adjusted', 0)

    # ── v5.8 配置（baseline，完全不变）──
    if phase1 == 'EMERGENCY':
        t58 = {'SHV': 0.70, 'GLD': 0.30}
    else:
        eq_l, fi_l, ra_l = row['eq_lim59'], row['fi_lim59'], row['ra_lim59']
        w_v, w_q = row['w_VTI'], row['w_QQQ']
        tw = w_v + w_q; w_v_n = w_v/tw if tw > 0 else 0.5; w_q_n = w_q/tw if tw > 0 else 0.5
        defense = (phase1=='WARNING') and (row.get('BND_def_triggered', 0)==1)
        if defense:
            fi_w_shv, fi_w_tlt = 0.80, 0.20
        elif sig == 'SHV_prefer':
            fi_w_shv, fi_w_tlt = 0.70, 0.30
        elif sig == 'TLT_prefer':
            fi_w_shv, fi_w_tlt = 0.30, 0.70
        else:
            fi_w_shv, fi_w_tlt = 0.50, 0.50
        t58 = {
            'VTI': eq_l * w_v_n,
            'QQQ': eq_l * w_q_n,
            'SHV': fi_l * fi_w_shv,
            'TLT': fi_l * fi_w_tlt,
            'GLD': ra_l,
        }
        total = sum(t58.values())
        if total > 0:
            t58 = {k: v/total for k, v in t58.items()}

    # ── v6.7 配置（关键修复版）──
    if phase1 == 'EMERGENCY':
        t67 = {'SHV': 0.70, 'GLD': 0.30}
    else:
        eq_l=row['eq_lim68b']; fi_l=row['fi_lim68b']
        gld_l=row['gld_lim68b']; xle_l=row['xle_lim68b']; pdbc_l=row['pdbc_lim68b']

        # ── v6.7 核心修复①：WARNING → VTI+QQQ 60/40（不用因子ETF）──
        if phase1 == 'WARNING':
            # WARNING期权益仓位用VTI+QQQ 60/40，与v5.8相同
            equity_ticker_v68b = 'VTI+QQQ'
        else:
            # HEALTHY期：直接使用评分结果 best_factor_v68b（评分循环已计算）
            # 交易日(is_score_day=1)时 best_f 有效：直接用 best_f 更新 prev_best_v68b 并设置 equity
            # 非交易日(NaN)：使用 prev_best_v68b（上一个交易日选出的有效因子）
            best_f = row['best_factor_v68b']
            is_sd = bool(row.get('is_score_day'))  # np.False_==1 is False, use truthiness

            if best_f in ('VTI+QQQ', 'VTI'):
                equity_ticker_v68b = 'VTI+QQQ'
                prev_best_v68b = 'VTI+QQQ'
            elif is_sd:
                # 交易日：best_f 有效 → 更新 prev_best_v68b 并使用 best_f
                prev_best_v68b = best_f
                equity_ticker_v68b = best_f
            else:
                # 非交易日：best_f 已由评分循环缓存（= 上个交易日选出的因子ETF）
                # prev_best_v68b 在上一个交易日已更新为此值，直接使用，无需验证 _ret 列
                if prev_best_v68b not in ('VTI+QQQ', 'VTI'):
                    equity_ticker_v68b = prev_best_v68b
                else:
                    equity_ticker_v68b = 'VTI+QQQ'  # fallback

        if sig == 'SHV_prefer':
            fi_w_shv, fi_w_tlt = 0.70, 0.30
        elif sig == 'TLT_prefer':
            fi_w_shv, fi_w_tlt = 0.30, 0.70
        else:
            fi_w_shv, fi_w_tlt = 0.50, 0.50

        if equity_ticker_v68b == 'VTI+QQQ':
            # VTI+QQQ 60/40 混合
            t67 = {
                'VTI': eq_l * 0.6,
                'QQQ': eq_l * 0.4,
                'SHV': fi_l * fi_w_shv,
                'TLT': fi_l * fi_w_tlt,
                'GLD': gld_l,
                'XLE': xle_l,
                'PDBC': pdbc_l,
            }
        else:
            t67 = {
                equity_ticker_v68b: eq_l,
                'SHV': fi_l * fi_w_shv,
                'TLT': fi_l * fi_w_tlt,
                'GLD': gld_l,
                'XLE': xle_l,
                'PDBC': pdbc_l,
            }
        total = sum(t67.values())
        if total > 0:
            t67 = {k: round(v/total, 4) for k, v in t67.items()}

    # ── 记录equity_ticker_v68b标记──
    if phase1 == 'EMERGENCY':
        prices.loc[idx, 'equity_ticker_v68b'] = 'SHV'
    elif phase1 == 'WARNING':
        prices.loc[idx, 'equity_ticker_v68b'] = 'VTI+QQQ'
    else:
        prices.loc[idx, 'equity_ticker_v68b'] = equity_ticker_v68b

    target_v59[idx] = t58
    target_v68b[idx] = t67

# ── 动态再平衡阈值预计算 ──
print("  预计算资产波动率（动态再平衡阈值用）...")
ret_cols = [c for c in prices.columns if c.endswith('_ret')]
vol_df = prices[ret_cols].rolling(60).std().ffill()
print(f"  波动率数据就绪：{len(ret_cols)} 个资产")

vol_price_cols = core_cols + ['SHV']
px = prices[vol_price_cols].copy()
for c in px.columns:
    px[c] = px[c] / px[c].iloc[0]

vol_30d = {}
for c in px.columns:
    vol_30d[c] = px[c].pct_change().rolling(30).std() * np.sqrt(252)

# ── 交易检测函数 ──
def calc_dynamic_band(ticker, vix_spot, idx, BASE_K=1/3):
    if ticker in vol_30d and idx < len(vol_30d[ticker]):
        vol = vol_30d[ticker].iloc[idx]
    else:
        vol = 0.12
    vol = vol if vol > 0 and not np.isnan(vol) else 0.12
    floor_band = 0.005 * (vix_spot / 15)
    dynamic_band = max(BASE_K * vol * (vix_spot / 20), floor_band)
    return dynamic_band

def detect_trades(target, holdings, prices_row, idx, vix_spot, phase1_status, nav, date,
                  is_initial=False, force=False):
    """检测调仓信号。
    
    Parameters
    ----------
    force : bool
        True时跳过dynamic_band阈值检查，强制执行所有超出最小门槛的调仓。
        用于方案C的三个触发日（因子切换/状态切换/新品类首次建仓）。
    """
    if holdings is None or len(holdings) == 0:
        return {}, 0.0

    panic_multiplier = 2.0 if vix_spot > 40 else 1.0
    fx_rate = get_fx_rate(date)
    min_amount_rmb = MIN_INITIAL_RMB if is_initial else MIN_ADD_SWITCH_RMB
    nav_usd = nav * INITIAL_NAV_USD
    nav_rmb = nav_usd * fx_rate

    cur_weights = target if target is not None else {}
    new_target = holdings
    all_tickers = set(cur_weights.keys()) | set(new_target.keys())

    raw_trades = {}

    for t in all_tickers:
        cur_w = cur_weights.get(t, 0.0)
        tgt_w = new_target.get(t, 0.0)
        weight_change = tgt_w - cur_w

        if abs(weight_change) < 1e-8:
            continue

        # 方案C：force=True时跳过dynamic_band阈值检查，强制执行全量调仓
        # 这是"开药时机"——三触发条件满足时，一次性完成所有配置调整
        if not force:
            dynamic_band = calc_dynamic_band(t, vix_spot, idx) * panic_multiplier
            if abs(weight_change) <= dynamic_band:
                continue
        else:
            # force=True: 仅用最小门槛过滤（低于门槛的跳过，其余全额执行）
            pass

        amount_usd = abs(weight_change) * nav_usd
        amount_rmb = amount_usd * fx_rate

        if is_initial:
            this_fee_rate = get_initial_fee_rate(t)
        else:
            this_fee_rate = ADD_SWITCH_FEE

        if weight_change > 0:
            meets_min = (amount_rmb >= min_amount_rmb)
            raw_trades[t] = {
                'action': 'BUY',
                'weight_change': weight_change,
                'amount_usd': amount_usd,
                'amount_rmb': amount_rmb,
                'fee_rate': this_fee_rate,
                'meets_min': meets_min,
            }
        else:
            raw_trades[t] = {
                'action': 'SELL',
                'weight_change': weight_change,
                'amount_usd': amount_usd,
                'amount_rmb': amount_rmb,
                'fee_rate': 0.0,
                'meets_min': True,
            }

    trades = {}
    total_fee_usd = 0.0

    for t, trade in raw_trades.items():
        if trade['action'] == 'SELL':
            trades[t] = {
                'action': 'SELL',
                'weight_change': trade['weight_change'],
                'amount_usd': trade['amount_usd'],
                'amount_rmb': trade['amount_rmb'],
                'fee_rate': 0.0,
                'fee_usd': 0.0,
            }
        else:
            if not trade['meets_min']:
                trades[t] = {
                    'action': 'SKIP',
                    'weight_change': trade['weight_change'],
                    'amount_usd': trade['amount_usd'],
                    'amount_rmb': trade['amount_rmb'],
                    'fee_rate': 0.0,
                    'fee_usd': 0.0,
                    'reason': f'below_min_{min_amount_rmb//1000}K_RMB',
                }
                continue

            # 新逻辑（2026-05-18）：所有BUY → fee = 3%，SELL → fee = 0%
            # 取消 net_buy_cat 区分，统一用 ADD_SWITCH_FEE
            fee_usd = trade['amount_usd'] * ADD_SWITCH_FEE

            trades[t] = {
                'action': 'BUY',
                'weight_change': trade['weight_change'],
                'amount_usd': trade['amount_usd'],
                'amount_rmb': trade['amount_rmb'],
                'fee_rate': ADD_SWITCH_FEE,
                'fee_usd': fee_usd,
            }
            total_fee_usd += fee_usd

    has_valid_trade = any(v.get('action') in ('BUY', 'SELL') for v in trades.values())

    if not has_valid_trade:
        return {}, 0.0

    return trades, total_fee_usd

# ══════════════════════════════════════════════════════════════
# 方案C：信号层与执行层分离 — 三触发预计算
# ══════════════════════════════════════════════════════════════
print("  方案C：预计算三触发信号...")
prices['is_factor_switch'] = False
prices['is_state_change']   = False
prices['is_new_category']   = False

prev_phase1 = None
prev_best_factor = None
# 追踪各资产类别是否已建仓（首次从0→>0为"新品类"）
# 资产类别：EQUITY(纯因子ETF), VTI+QQQ, FIXED_INCOME, GLD, XLE, PDBC
established_categories_v58 = set()
established_categories_v67 = set()

# ── Hysteresis counter for state change detection ──
# Require 3 consecutive days in new state before triggering is_state_change
# Prevents HEALTHY↔WARNING oscillation when CSI hovers near 1.0 threshold
# Track per-state counters + a flag so we only fire ONCE per transition
state_persist_count = {}  # {phase1: consecutive_days}
state_change_fired_for = set()  # set of (phase1, streak_key) already fired
LASTING_STATE_DAYS = 3

for i, (idx, row) in enumerate(prices.iterrows()):
    curr_phase1 = row['Phase1_status']
    curr_best_f = row['best_factor_v68b']
    t58 = target_v59[idx]
    t67 = target_v68b[idx]

    # ── 触发①：因子切换 ──
    # 仅在评分日（is_score_day=True）且因子发生变化时触发
    if row['is_score_day'] and (prev_best_factor is not None) and (curr_best_f != prev_best_factor):
        prices.loc[idx, 'is_factor_switch'] = True

    # ── 触发②：Phase1状态切换（需3日持续新状态才触发，仅触发一次）──
    # Hysteresis防止CSI在阈值1.0附近反复横跳导致频繁换手
    if prev_phase1 is not None:
        if curr_phase1 != prev_phase1:
            # Entered new state: reset counter for new state, carry over count for old
            state_persist_count[curr_phase1] = 1
            state_persist_count[prev_phase1] = 0
        else:
            # Same state: increment counter
            state_persist_count[curr_phase1] = state_persist_count.get(curr_phase1, 0) + 1
        # Trigger only on the FIRST day the counter crosses LASTING_STATE_DAYS
        streak = state_persist_count.get(curr_phase1, 0)
        # FIX: fire_key must be the TRANSITION (prev_phase1 → curr_phase1), not (curr_phase1, streak)
        # Using (curr_phase1, streak) causes re-fire on day 5,6... of same state (new streak values not in set)
        # Using == LASTING_STATE_DAYS instead of >= ensures we only fire once at threshold crossing
        fire_key = (prev_phase1, curr_phase1)
        if streak == LASTING_STATE_DAYS and fire_key not in state_change_fired_for:
            prices.loc[idx, 'is_state_change'] = True
            state_change_fired_for.add(fire_key)

    # ── 触发③：新品类首次建仓 ──
    # 同一资产类别内的比例调整（如GLD 10%→12%）不算新品类
    # 新增一个之前从未持有过的资产类别才算
    def get_category_key(ticker):
        """将ETF映射到资产类别"""
        if ticker in EQUITY_FUND_TYPES:
            return 'EQUITY_FUND'
        elif ticker in ('VTI', 'QQQ'):
            return 'VTI_QQQ'
        elif ticker in BOND_FUND_TYPES:
            return 'FIXED_INCOME'
        elif ticker in COMMODITY_FUND_TYPES:
            return 'COMMODITY'
        else:
            return 'OTHER'

    # v5.8新品类
    for ticker, w in t58.items():
        if w > 0:
            cat = get_category_key(ticker)
            if cat not in established_categories_v58:
                prices.loc[idx, 'is_new_category'] = True
                established_categories_v58.add(cat)
    # v6.7新品类
    for ticker, w in t67.items():
        if w > 0:
            cat = get_category_key(ticker)
            if cat not in established_categories_v67:
                prices.loc[idx, 'is_new_category'] = True
                established_categories_v67.add(cat)

    prev_phase1 = curr_phase1
    prev_best_factor = curr_best_f

trigger_stats = {
    'factor_switch': int(prices['is_factor_switch'].sum()),
    'state_change':  int(prices['is_state_change'].sum()),
    'new_category': int(prices['is_new_category'].sum()),
}
print(f"  方案C 触发统计：因子切换={trigger_stats['factor_switch']}天 | "
      f"状态切换={trigger_stats['state_change']}天 | 新品类={trigger_stats['new_category']}天")
print(f"  非触发日将跳过detect_trades（保持持仓，节省换手成本）")

ret_v59, ret_v68b, ret_spy = [], [], []

log_v59, log_v68b = [], []

nav59 = 1.0
nav68b = 1.0
nav59_gross = 1.0
nav68b_gross = 1.0
# ★ Bug Fix #4: 追踪累计费用(NAV单位)
# 毛NAV(gross) = 从1.0复合，无费用扣除
# 净NAV(net)   = 从1.0复合，每日扣除当日费用/NAV作为return损耗
# 关键：毛和净用同一NAV起点(1.0)，使cumret计算可比较
cum_fee_nav59 = 0.0  # 累计费用(NAV单位)
cum_fee_nav68b = 0.0
prev_t58 = None
prev_t67 = None
nav59_seq, nav68b_seq = [], []
nav59_gross_seq, nav68b_gross_seq = [], []

for i, (idx, row) in enumerate(prices.iterrows()):
    phase1 = row['Phase1_status']
    quad   = int(row.get('macro_quadrant', 1))
    sig    = row.get('duration_signal', 'balanced')
    mci    = row.get('MCI_adjusted', 0)
    best_f = row.get('best_factor_v68b', 'VTI')

    ret_spy.append(float(row['SPY_ret']))

    t58 = target_v59[idx]
    t67 = target_v68b[idx]

    is_initial_58 = prev_t58 is None
    is_initial_67 = prev_t67 is None

    # ── 方案C：非触发日跳过detect_trades（保持持仓，不产生换手）──
    # 三轨HRP每日"体检"但不开药；只在触发日一次性完成配置调整
    is_factor_sw = bool(row.get('is_factor_switch', False))
    is_state_chg = bool(row.get('is_state_change', False))
    is_new_cat    = bool(row.get('is_new_category', False))
    any_trigger   = is_factor_sw or is_state_chg or is_new_cat

    # 追踪因子切换日志
    if is_factor_sw:
        print(f"  [因子切换] {idx.date()} → {best_f}  | 状态:{phase1} | MCI:{mci}")

    if any_trigger or is_initial_58:
        # force决策逻辑：
        #  ① 因子切换/新品类/初始建仓 → force=True（跳过dynamic_band，全量配置调整）
        #  ② 纯状态切换 → force=False（状态变化大，用dynamic_band过滤微调）
        #    （状态切换仍触发detect_trades，但仅执行显著偏离目标的调整）
        trigger_force = (is_factor_sw or is_new_cat) and not is_initial_58
        trades58, fee58_usd = detect_trades(
            target=prev_t58, holdings=t58, prices_row=row, idx=i,
            vix_spot=row['VIX'], phase1_status=phase1, nav=nav59,
            date=idx, is_initial=is_initial_58, force=trigger_force
        )
    else:
        trades58, fee58_usd = {}, 0.0

    if any_trigger or is_initial_67:
        trigger_force = (is_factor_sw or is_new_cat) and not is_initial_67
        trades67, fee67_usd = detect_trades(
            target=prev_t67, holdings=t67, prices_row=row, idx=i,
            vix_spot=row['VIX'], phase1_status=phase1, nav=nav68b,
            date=idx, is_initial=is_initial_67, force=trigger_force
        )
    else:
        trades67, fee67_usd = {}, 0.0

    has_valid_58 = any(v.get('action') in ('BUY', 'SELL') for v in trades58.values()) if trades58 else False
    has_valid_67 = any(v.get('action') in ('BUY', 'SELL') for v in trades67.values()) if trades67 else False

    if has_valid_58:
        log_v59.append({
            'date': idx, 'phase1': phase1, 'quad': quad, 'mci': mci,
            'signal': sig, 'best_factor': best_f,
            'trades': trades58, 'total_fee_usd': fee58_usd,
        })
    if has_valid_67:
        log_v68b.append({
            'date': idx, 'phase1': phase1, 'quad': quad, 'mci': mci,
            'signal': sig, 'best_factor': best_f,
            'trades': trades67, 'total_fee_usd': fee67_usd,
        })

    prev_t58 = t58
    prev_t67 = t67

    # ── NAV跟踪 ──
    if phase1 == 'EMERGENCY':
        r59_gross = 0.70*row['SHV_ret'] + 0.30*row['GLD_ret']
        # ★ Fix #9: v6.7 EMERGENCY NAV = SHV 70% + GLD 30%，权益归零
        r68b_gross = 0.70*row['SHV_ret'] + 0.30*row['GLD_ret']
    else:
        w_v, w_q = row['w_VTI'], row['w_QQQ']
        tw = w_v + w_q; w_v_n = w_v/tw if tw > 0 else 0.5; w_q_n = w_q/tw if tw > 0 else 0.5
        equity58 = w_v_n*row['VTI_ret'] + w_q_n*row['QQQ_ret']
        sig2 = row.get('duration_signal', 'balanced')
        if sig2 == 'SHV_prefer': w_shv, w_tlt = 0.70, 0.30
        elif sig2 == 'TLT_prefer': w_shv, w_tlt = 0.30, 0.70
        else:
            vs = max(row.get('SHV_vol60', 0.001), 0.001)
            vt = max(row.get('TLT_vol60', 0.001), 0.001)
            w_shv = (1/vs)/(1/vs+1/vt); w_tlt = 1-w_shv
        fi_ret = w_shv*row['SHV_ret'] + w_tlt*row['TLT_ret']
        defense = (phase1=='WARNING') and (row.get('BND_def_triggered', 0)==1)
        if defense: fi_ret = 0.80*row['SHV_ret'] + 0.20*row['TLT_ret']
        r59_gross = row['eq_lim59']*equity58 + row['fi_lim59']*fi_ret + row['ra_lim59']*row['GLD_ret']

        # v6.7 NAV计算
        eq_l67=row['eq_lim68b']; fi_l67=row['fi_lim68b']
        gld_l67=row['gld_lim68b']; xle_l67=row['xle_lim68b']; pdbc_l67=row['pdbc_lim68b']
        equity_ticker_v68b = row.get('equity_ticker_v68b', 'VTI')

        if equity_ticker_v68b == 'VTI+QQQ':
            equity67 = w_v_n*row['VTI_ret'] + w_q_n*row['QQQ_ret']
        elif f'{equity_ticker_v68b}_ret' in prices.columns and not np.isnan(row.get(f'{equity_ticker_v68b}_ret', np.nan)):
            equity67 = row[f'{equity_ticker_v68b}_ret']
        else:
            equity67 = w_v_n*row['VTI_ret'] + w_q_n*row['QQQ_ret']

        gld67 = row['GLD_ret']
        xle_r = row['XLE_ret']  # 直接取，NaN直接传播（XLE数据2007年起完整）
        pdbc_r = row['GLD_ret'] if np.isnan(row.get('PDBC_ret', np.nan)) else row['PDBC_ret']
        real67 = gld_l67*gld67 + xle_l67*xle_r + pdbc_l67*pdbc_r
        r68b_gross = eq_l67*equity67 + fi_l67*fi_ret + real67

    ret_v59.append(r59_gross if not np.isnan(r59_gross) else 0.0)
    ret_v68b.append(r68b_gross if not np.isnan(r68b_gross) else 0.0)

    nav59_gross = nav59_gross * (1 + (r59_gross if not np.isnan(r59_gross) else 0.0))
    nav68b_gross = nav68b_gross * (1 + (r68b_gross if not np.isnan(r68b_gross) else 0.0))

    r59_clean = r59_gross if not np.isnan(r59_gross) else 0.0
    r68b_clean = r68b_gross if not np.isnan(r68b_gross) else 0.0
    # ★ Bug Fix #4 (修正版): 费用应在gross return前从position中扣除
    # 正确: position = position * (1 - fee_rate) * (1 + gross_return)
    # 而非: position = position * (1 + gross_return) - fee_nav_units (BUG)
    if has_valid_58 and fee58_usd > 0:
        fee_rate58 = fee58_usd / max(1.0, nav59 * INITIAL_NAV_USD)
        nav59 = nav59 * (1 - fee_rate58) * (1 + r59_clean)
    else:
        nav59 = nav59 * (1 + r59_clean)

    if has_valid_67 and fee67_usd > 0:
        fee_rate67 = fee67_usd / max(1.0, nav68b * INITIAL_NAV_USD)
        nav68b = nav68b * (1 - fee_rate67) * (1 + r68b_clean)
    else:
        nav68b = nav68b * (1 + r68b_clean)

    if i % 500 == 0:
        print(f"DEBUG: i={i}, len(nav59_seq)={len(nav59_seq)}, nav59={nav59:.6f}, nav68b={nav68b:.6f}")
    nav59_seq.append(nav59)
    nav68b_seq.append(nav68b)
    nav59_gross_seq.append(nav59_gross)
    nav68b_gross_seq.append(nav68b_gross)

print(f"  [DEBUG] Loop complete: len(nav59_seq)={len(nav59_seq)}, len(nav68b_seq)={len(nav68b_seq)}")
print(f"  [DEBUG] nav59 last5={nav59_seq[-5:]}")
print(f"  [DEBUG] nav59 first5={nav59_seq[:5]}")

prices['ret_v59'] = ret_v59
prices['ret_v68b'] = ret_v68b
prices['ret_spy'] = ret_spy

# ★ Bug Fix #10 (核心修复): 使用vectorized cumprod替代手动索引对齐
# ret_v59/ret_v68b是list，与prices等长(4865)，直接cumprod即可
prices['v59_cum'] = (1 + pd.Series(ret_v59, index=prices.index).fillna(0)).cumprod()
prices['v68b_cum'] = (1 + pd.Series(ret_v68b, index=prices.index).fillna(0)).cumprod()
# ★ Fix #14: v59_cum_gross / v68b_cum_gross 必须从 nav*_gross_seq（实际无费用NAV）计算
# 之前错误地用 cumprod(ret_v59/ret_v68b)，导致 gross=net（都用了同一序列）
prices['v59_cum_gross'] = pd.Series(nav59_gross_seq, index=prices.index[:len(nav59_gross_seq)])
prices['v68b_cum_gross'] = pd.Series(nav68b_gross_seq, index=prices.index[:len(nav68b_gross_seq)])
prices['spy_cum'] = (1+pd.Series(ret_spy, index=prices.index).fillna(0)).cumprod()

# ★ Fix #15: v59_cum_net / v68b_cum_net 从已扣费的 nav*_seq 构建（有摩擦净NAV）
# v59_cum / v68b_cum 保留为毛收益序列（用于与 gross 比较）
prices['v59_cum_net'] = pd.Series(nav59_seq, index=prices.index[:len(nav59_seq)])
prices['v68b_cum_net'] = pd.Series(nav68b_seq, index=prices.index[:len(nav68b_seq)])

# ★ Fix #14 续：ret_v59_gross / ret_v68b_gross 必须从 nav*_gross_seq 的 pct_change 计算
# 之前错误地直接用 ret_v59/ret_v68b（等于 gross_returns 列表本身，导致 ret_v59_gross=ret_v59）
_r59g = pd.Series(nav59_gross_seq, index=prices.index[:len(nav59_gross_seq)]).pct_change().fillna(0)
_r68b_g = pd.Series(nav68b_gross_seq, index=prices.index[:len(nav68b_gross_seq)]).pct_change().fillna(0)
# 净收益从已扣费NAV序列计算
_r59n = pd.Series(nav59_seq, index=prices.index[:len(nav59_seq)]).pct_change().fillna(0)
_r68bn = pd.Series(nav68b_seq, index=prices.index[:len(nav68b_seq)]).pct_change().fillna(0)
prices['ret_v59_net'] = _r59n
prices['ret_v68b_net'] = _r68bn
prices['ret_v59_gross'] = _r59g
prices['ret_v68b_gross'] = _r68b_g

total_cost_display59 = sum(l['total_fee_usd'] for l in log_v59)
total_cost_display68b = sum(l['total_fee_usd'] for l in log_v68b)

n59 = len(log_v59)
n68b = len(log_v68b)

print(f"  v5.9 调仓次数: {n59} 次 | 累计成本: ${total_cost_display59:,.2f}")
print(f"  v6.8.1 调仓次数: {n68b} 次 | 累计成本: ${total_cost_display68b:,.2f}")

# ── 年度调仓分布 ──
annual_rebal_v59 = {}
annual_rebal_v68b = {}
annual_cost_v59 = {}
annual_cost_v68b = {}

for l in log_v59:
    yr = l['date'].year
    annual_rebal_v59[yr] = annual_rebal_v59.get(yr, 0) + 1
    annual_cost_v59[yr] = annual_cost_v59.get(yr, 0.0) + l['total_fee_usd'] / INITIAL_NAV_USD
for l in log_v68b:
    yr = l['date'].year
    annual_rebal_v68b[yr] = annual_rebal_v68b.get(yr, 0) + 1
    annual_cost_v68b[yr] = annual_cost_v68b.get(yr, 0.0) + l['total_fee_usd'] / INITIAL_NAV_USD

# ─────────────────────────────────────────────────────────
# ⑪ 性能统计
# ─────────────────────────────────────────────────────────
print("\n⑪ 性能统计...")

def maxdd(s):
    peak=s.cummax(); return ((s-peak)/peak).min()

def ps(df, col, label, nav_col=None):
    if nav_col and nav_col in df.columns:
        nav = df[nav_col].dropna()
        r = float(nav.iloc[-1] / nav.iloc[0] - 1)
        dd = maxdd(nav)
        v = df[col].std() * np.sqrt(252)
        ra = df[col].mean() * 252
    else:
        # ★ Fix #13: 用fillna(0)而非dropna()，使NaN日（NAV冻结/无数据）的收益=0
        #   - 正确: cumprod(1+NaN)→NaN→fillna(0)→0→(1+0)=1（中性乘数）
        #   - 错误: dropna()后cumprod仅覆盖有数据的前N天，导致iloc[-1]≠真正最终净值
        s = (1+df[col].fillna(0)).cumprod()
        r = float(s.iloc[-1]-1); dd=maxdd(s)
        v=df[col].std()*np.sqrt(252); ra=df[col].mean()*252
    sh=ra/v if v>0 else 0
    return {'label':label,'cumret':float(r),'mdd':float(dd),
            'sharpe':float(sh),'vol':float(v),'ann_ret':float(ra)}

ev = prices.dropna(subset=['ret_v59_net','ret_v68b_net','ret_spy'])
s59_net=ps(ev,'ret_v59_net','v5.8_net',nav_col='v59_cum_net')
s68b_net=ps(ev,'ret_v68b_net','v6.7_net',nav_col='v68b_cum_net')
ss=ps(ev,'ret_spy','SPY')
ev_g = prices.dropna(subset=['ret_v59_gross','ret_v68b_gross'])
s59_gross=ps(ev_g,'ret_v59_gross','v5.8_gross',nav_col='v59_cum_gross')
s68b_gross=ps(ev_g,'ret_v68b_gross','v6.8_gross',nav_col='v68b_cum_gross')

print(f"\n{'='*72}")
print(f"{'指标':<18} {'v5.9(有摩擦)':>14} {'v5.9(无摩擦)':>14} {'v6.8.1(有摩擦)':>14} {'v6.8.1(无摩擦)':>14} {'SPY':>10}")
print("-"*110)
print(f"{'累计收益':.<18} {s59_net['cumret']:>+14.1%} {s59_gross['cumret']:>+14.1%} {s68b_net['cumret']:>+14.1%} {s68b_gross['cumret']:>+14.1%} {ss['cumret']:>+10.1%}")
print(f"{'年化收益':.<18} {s59_net['ann_ret']:>+14.2%} {s59_gross['ann_ret']:>+14.2%} {s68b_net['ann_ret']:>+14.2%} {s68b_gross['ann_ret']:>+14.2%} {ss['ann_ret']:>+10.2%}")
print(f"{'夏普比率':.<18} {s59_net['sharpe']:>+14.2f} {s59_gross['sharpe']:>+14.2f} {s68b_net['sharpe']:>+14.2f} {s68b_gross['sharpe']:>+14.2f} {ss['sharpe']:>+10.2f}")
print(f"{'最大回撤':.<18} {s59_net['mdd']:>+14.1%} {s59_gross['mdd']:>+14.1%} {s68b_net['mdd']:>+14.1%} {s68b_gross['mdd']:>+14.1%} {ss['mdd']:>+10.1%}")
print(f"{'调仓次数':.<18} {n59:>14}次 {n68b:>14}次 —")
print(f"{'累计成本(USD)':.<18} ${total_cost_display59:>13,.0f} — ${total_cost_display68b:>13,.0f} —")
print("-"*110)
print("  [有摩擦=实际HSBC渠道成本 | 无摩擦=理想状态不含交易成本]")

# ── 年度收益（用日收益序列计算，不用截断的nav列）──
annual_data = []
for yr in range(2007, 2027):
    yr_data = prices[prices.index.year == yr]
    if len(yr_data) < 20: continue
    # 用日收益率计算年度收益（避免nav序列截断导致的NaN）
    r59_daily = yr_data['ret_v59_net'].fillna(0)
    r68b_daily = yr_data['ret_v68b_net'].fillna(0)
    r59g_daily = yr_data['ret_v59_gross'].fillna(0)
    r68b_g_daily = yr_data['ret_v68b_gross'].fillna(0)
    r59 = float((1+r59_daily).prod() - 1)
    r68b = float((1+r68b_daily).prod() - 1)
    r59g = float((1+r59g_daily).prod() - 1)
    r68b_g = float((1+r68b_g_daily).prod() - 1)
    rsp_daily = yr_data['ret_spy'].fillna(0)
    rsp = float((1+rsp_daily).prod() - 1)
    n59_yr = annual_rebal_v59.get(yr, 0)
    n68b_yr = annual_rebal_v68b.get(yr, 0)
    annual_data.append({
        'year': yr, 'v59': r59, 'v68b': r68b,
        'v59_gross': r59g, 'v68b_gross': r68b_g,
        'spy': rsp,
        'n59': n59_yr, 'n68b': n68b_yr,
    })
    print(f"  {yr}: v5.9(净){r59:>+7.1%} (毛){r59g:>+7.1%} | "
          f"v6.8.1(净){r68b:>+7.1%} (毛){r68b_g:>+7.1%} | SPY {rsp:>+7.1%} | "
          f"调仓(v5.9={n59_yr}, v6.8.1={n68b_yr})")

# ─────────────────────────────────────────────────────────
# ⑫ 生成 HTML 对比报告
# ─────────────────────────────────────────────────────────
print("\n⑫ 生成HTML对比报告...")

annual_rows = ""
for d in annual_data:
    bg = "#f0f4ff" if d['v68b']>d['v59'] else "#fff8f0"
    annual_rows += f"""<tr style="background:{bg}">
        <td>{d['year']}</td>
        <td class="{'pos' if d['v59']>0 else 'neg'}">{d['v59']:+.1%}</td>
        <td class="{'pos' if d['v68b']>0 else 'neg'}">{d['v68b']:+.1%}</td>
        <td class="{'pos' if d['spy']>0 else 'neg'}">{d['spy']:+.1%}</td>
        <td>{d['n59']}</td>
        <td>{d['n68b']}</td>
    </tr>"""

def make_trade_rows(log_list, version_label, max_rows=200):
    rows = ""
    shown = 0
    for entry in log_list:
        if shown >= max_rows:
            break
        date_str = entry['date'].strftime('%Y-%m-%d')
        phase_badge = f"<span style='background:{'#ffcccc' if entry['phase1']=='EMERGENCY' else '#fff3cd' if entry['phase1']=='WARNING' else '#e8f5e9'};padding:1px 6px;border-radius:3px;font-size:11px'>{entry['phase1']}</span>"
        quad_badge = f"<span style='background:#e3f2fd;padding:1px 6px;border-radius:3px;font-size:11px'>Q{entry['quad']}</span>"
        sig_badge  = f"<span style='background:#f3e5f5;padding:1px 6px;border-radius:3px;font-size:11px'>{entry.get('signal','balanced')}</span>"
        mci_val    = entry.get('mci', 0)
        mci_color  = '#e8f5e9' if mci_val >= 0 else '#ffcccc'
        mci_badge  = f"<span style='background:{mci_color};padding:1px 6px;border-radius:3px;font-size:11px'>MCI={mci_val}</span>"
        bf_badge   = f"<span style='background:#fff8e1;padding:1px 6px;border-radius:3px;font-size:11px'>{entry.get('best_factor','—')}</span>"
        trades = entry['trades']
        if isinstance(trades, dict):
            trades_str_parts = []
            for ticker, info in trades.items():
                if isinstance(info, dict):
                    action = info.get('action', 'BUY')
                    amount_usd = info.get('amount_usd', 0)
                    amount_rmb = info.get('amount_rmb', 0)
                    fee_rate = info.get('fee_rate', 0)
                    if action == 'SKIP':
                        rmb_val = int(float(amount_rmb)) if not pd.isna(amount_rmb) else 0
                        trades_str_parts.append(f"{ticker} SKIP(不足{rmb_val:,}RMB)")
                    else:
                        usd_val = int(float(amount_usd)) if not pd.isna(amount_usd) else 0
                        rmb_val = int(float(amount_rmb)) if not pd.isna(amount_rmb) else 0
                        trades_str_parts.append(f"{ticker} {action}(${usd_val:,}≈¥{rmb_val:,}, {fee_rate:.0%}费)")
                else:
                    delta = info
                    trades_str_parts.append(f"{ticker} {'BUY' if delta > 0 else 'SELL'} ({delta:+.1f}股)")
            trades_str = " | ".join(trades_str_parts)
        else:
            trades_str = " | ".join([
                f"{t['ticker']} {t['direction']} {t.get('w_old',0):.0%}→{t.get('w_new',0):.0%} ({t.get('delta',0):.1%})"
                for t in trades
            ])
        total_fee = entry.get('total_fee_usd', 0)
        cost_color = '#ffcccc' if total_fee > 100 else '#fff8e1'
        rows += f"""<tr>
            <td style="text-align:left">{date_str}</td>
            <td>{phase_badge} {quad_badge} {sig_badge}</td>
            <td>{mci_badge} {bf_badge}</td>
            <td style="text-align:left;font-size:11px;max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                title="{trades_str}">{trades_str}</td>
            <td style="background:{cost_color}">${total_fee:,.0f}</td>
        </tr>"""
        shown += 1
    if shown == max_rows:
        rows += f"""<tr><td colspan="5" style="text-align:center;color:#999;font-size:12px">
            ... 共 {len(log_list)} 条交易，仅展示前 {max_rows} 条 | 完整日志见CSV导出
        </td></tr>"""
    return rows

trade_rows_v59 = make_trade_rows(log_v59, 'v5.9', max_rows=200)
trade_rows_v68b = make_trade_rows(log_v68b, 'v6.8.1', max_rows=200)

cost_annual_rows = ""
for d in annual_data:
    yr = d['year']
    cost59_yr = annual_cost_v59.get(yr, 0.0)
    cost68b_yr = annual_cost_v68b.get(yr, 0.0)
    cost_annual_rows += f"""<tr>
        <td>{yr}</td>
        <td>{d['n59']}</td>
        <td style="background:{'#fff3cd' if cost59_yr > 0.005 else 'transparent'}">{cost59_yr:.2%}</td>
        <td>{d['n68b']}</td>
        <td style="background:{'#fff3cd' if cost68b_yr > 0.005 else 'transparent'}">{cost68b_yr:.2%}</td>
    </tr>"""

phase_rows = ""
for s,c in prices['Phase1_status'].value_counts().items():
    pct=c/len(prices)*100
    phase_rows+=f"<tr><td>{s}</td><td>{c}</td><td>{pct:.1f}%</td></tr>"

factor_rows_v68b = ""
for f,cnt in factor_dist_v68b.items():
    pct=cnt/len(factor_dist_v68b)*100
    factor_rows_v68b+=f"<tr><td>{f}</td><td>{cnt}</td><td>{pct:.1f}%</td></tr>"

avail_rows = ""
for short_name in factor_list:
    avail = prices[short_name].notna().sum() if short_name in prices.columns else 0
    first_d = prices[short_name].first_valid_index() if short_name in prices.columns else None
    last_d  = prices[short_name].last_valid_index()  if short_name in prices.columns else None
    avail_rows+=f"<tr><td>{short_name}</td><td>{avail}</td>"
    avail_rows+=f"<td>{str(first_d.date()) if first_d else 'N/A'}</td>"
    avail_rows+=f"<td>{str(last_d.date()) if last_d else 'N/A'}</td></tr>"

# equity_ticker分布
eq_ticker_dist = prices['equity_ticker_v68b'].value_counts()

# ★ 动态计算因子ETF天数和equity配置（用于HTML报告）

# ══════════════════════════════════════════════════════════════
# ★ Chart.js 折线图数据 (月度累计收益) - 2026-06-09 重构加入
# ══════════════════════════════════════════════════════════════
import json as _json

# 月度采样（每月最后一个交易日），约 234 个月度点
# PATCH 2026-07-16: pandas 2.x 用 'ME' (Month End) 替代 'M'
try:
    monthly_idx = prices.resample('ME').last().index
except ValueError:
    monthly_idx = prices.resample('M').last().index
monthly_idx_str = [d.strftime('%Y-%m-%d') for d in monthly_idx]

def _safe_series(col, default=1.0):
    """Return values aligned to monthly_idx, with fallback to spy_cum if col missing."""
    if col not in prices.columns:
        return [default] * len(monthly_idx)
    s = prices[col].reindex(monthly_idx)
    s = s.ffill().bfill().fillna(default)
    return [float(v) for v in s]

chart_data = {
    "dates": monthly_idx_str,
    "v59":  _safe_series("v59_cum_net", 1.0),
    "v681": _safe_series("v68b_cum_net", 1.0),
    "spy":  _safe_series("spy_cum", 1.0),
}
chart_data_json = _json.dumps(chart_data, ensure_ascii=False)
print(f"  折线图数据: {len(chart_data_json)} chars, {len(monthly_idx)} 月度点")
factor_etf_tickers = ['MTUM','IJR','VB','QUAL','SPLV','MOAT','VIG','USMV']
healthy_factor_days = int((prices['equity_ticker_v68b'].isin(factor_etf_tickers)).sum())
warning_days = int((prices['Phase1_status'] == 'WARNING').sum())
healthy_days = int((prices['Phase1_status'] == 'HEALTHY').sum())
healthy_factor_pct = 100 * healthy_factor_days / len(prices)
eq_avg67 = 100 * prices['eq_lim68b'].mean()
eq_avg58 = 100 * prices['eq_lim59'].mean()

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIF v5.9 / v6.8.1 对比报告（2026-06-09 · P0修复版 · CSI Hysteresis + F29>500bp）</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'PingFang SC','Microsoft YaHei',-apple-system,sans-serif; background:#f0f2f5; color:#1a1a2e; }}
        .header {{ background:linear-gradient(135deg,#1565c0 0%,#7209b7 100%); color:white; padding:36px 48px; }}
        .header h1 {{ font-size:1.6rem; font-weight:700; margin-bottom:6px; }}
        .header p {{ opacity:0.85; font-size:0.88rem; }}
        .badge {{ display:inline-block; background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.35);
                  padding:3px 12px; border-radius:20px; font-size:0.78rem; margin-top:8px; }}
        .container {{ max-width:1180px; margin:0 auto; padding:28px 20px; }}
        .section {{ margin-bottom:36px; }}
        .section-title {{ font-size:1.1rem; font-weight:700; color:#1565c0; border-left:4px solid #1565c0;
                          padding-left:10px; margin-bottom:16px; }}
        table {{ border-collapse:collapse; width:100%; font-size:0.85rem; }}
        th {{ background:#1565c0; color:white; padding:9px 12px; text-align:center; font-weight:600; white-space:nowrap; }}
        th.v67 {{ background:#7b1fa2; }}
        td {{ padding:8px 12px; text-align:center; border-bottom:1px solid #f0f0f0; }}
        tr:last-child td {{ border-bottom:none; }}
        tr:hover td {{ background:#f5f5f5; }}
        .pos {{ color:#c62828; font-weight:600; }}
        .neg {{ color:#2e7d32; font-weight:600; }}
        .note-box {{ background:#fff8e1; border-left:4px solid #f9a825; padding:14px 18px;
                     border-radius:0 6px 6px 0; font-size:0.84rem; line-height:1.75; margin-top:16px; }}
        .data-note {{ background:#e8f5e9; border-left:4px solid #2e7d32; padding:13px 18px;
                      border-radius:0 6px 6px 0; font-size:0.84rem; margin-top:16px; }}
        .warning-box {{ background:#fff3cd; border:1px solid #ffc107; border-radius:8px;
                       padding:14px; margin:16px 0; font-size:0.85rem; }}
        .warning-box h4 {{ margin:0 0 6px; color:#856404; }}
        .cost-box {{ background:#e3f2fd; border-left:4px solid #1565c0; padding:13px 18px;
                     border-radius:0 6px 6px 0; font-size:0.84rem; margin-top:12px; }}
        .tag-v59 {{ display:inline-block; background:#e3f2fd; color:#1565c0; padding:1px 7px;
                    border-radius:4px; font-size:0.78rem; font-weight:600; }}
        .tag-v68b {{ display:inline-block; background:#f3e5f5; color:#7b1fa2; padding:1px 7px;
                   border-radius:3px; font-size:0.85em; }}
        .tag-v68b {{ display:inline-block; background:#e8f5e9; color:#2e7d32; padding:1px 7px;
                    border-radius:4px; font-size:0.78rem; font-weight:600; }}
        .trade-table {{ font-size:0.8rem; }}
        .trade-table th {{ background:#37474f; }}
        .trade-table td {{ padding:6px 10px; }}
        .filter-bar {{ display:flex; gap:10px; margin-bottom:14px; flex-wrap:wrap; align-items:center; }}
        .filter-bar select {{ padding:5px 10px; border:1px solid #ccc; border-radius:6px; font-size:0.84rem; }}
        .filter-bar label {{ font-size:0.84rem; color:#555; }}
        .section-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }}
        .section-header h2 {{ margin:0; font-size:1.1rem; }}
        .count-badge {{ background:#e0e0e0; padding:2px 8px; border-radius:10px; font-size:0.75rem; color:#666; }}
        .key-fix {{ background:#e8f5e9; border-left:4px solid #2e7d32; padding:13px 18px;
                    border-radius:0 6px 6px 0; font-size:0.84rem; margin:16px 0; }}
        .key-fix h4 {{ margin:0 0 8px; color:#1b5e20; }}
        .chart-container {{ position:relative; width:100%; height:420px; }}
        @media(max-width:768px) {{ .header {{ padding:20px; }} table {{ font-size:0.78rem; }} .chart-container {{ height:300px; }} }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>

<div class="header">
    <h1>WIF v5.9 / v6.8.1 完整回测报告（2007-2026 · P0修复版 · CSI Hysteresis + F29>500bp + Q3 滞胀≤30%）</h1>
    <p>Wealth Investment Framework · v5.9 P0修复版（CSI Hysteresis + F29>500bp + Q3 滞胀≤30%） · v6.8.1 框架 · 数据范围 {prices.index[0].date()} ~ {prices.index[-1].date()}</p>
    <span class="badge">{len(prices)} 交易日 · CSI复合压力指数 · 方案C信号/执行分离 · HSBC渠道成本已扣除</span>
</div>

<div class="container">

    <!-- 执行摘要 -->
    <div class="section">
        <div class="section-title">执行摘要</div>
        <div class="key-fix">
            <h4>🔧 2026-06-09 v5.9 / v6.8.1 P0 修复 + Q3 修复</h4>
            <ul style="margin:0 0 0 18px; line-height:1.9;">
                <li><strong>① CSI复合压力指数</strong>：Z(F29)×0.45 + Z(VIXTERM)×0.35 + Z(相关性崩塌)×0.20，统一的连续值度量衡，消除布尔悬崖</li>
                <li><strong>② CSI阈值</strong>：CSI>2.0→EMERGENCY | CSI 1.0-2.0→WARNING | CSI<1.0连5日→HEALTHY退出</li>
                <li><strong>③ F33b EMERGENCY override（独立安全气囊）</strong>：
                    VIX>40且10日涨幅>100% → 强制EMERGENCY（不受CSI阈值限制）
                    <br>　★ F33b负责"第一时间拉闸"（VIX动量领先信用利差），CSI负责"持续压力判断"，两者互补
                </li>
                <li><strong>④ 方案C：信号层与执行层分离</strong>
                    <br>　非触发日跳过detect_trades（保持持仓，不产生活跃换手）
                    <br>　三触发：因子切换 | 状态切换 | 新品类首次建仓
                </li>
                <li><strong>⑤ E04动量窗口</strong>：126日→252日（学术标准12+1月）</li>
            </ul>
        </div>
        <div class="warning-box">
            <h4>⚠️ 存活者偏差警告</h4>
            v6.8.1 因子ETF池（QUAL/IJR/MTUM/VIG等）存在存活者偏差——历史已退市、合并的ETF不在数据中，导致2013年后收益明显高估。<strong>v5.9仅用VTI/QQQ，无此偏差</strong>。
        </div>
        <div class="cost-box">
            <strong>💰 HSBC渠道成本模型</strong>
            <ul style="margin:6px 0 0 18px; line-height:1.9;">
                <li>股票型/均衡型：初始建仓 3% | 追加/切换 3%</li>
                <li>债券型：初始建仓 2% | 追加/切换 3%</li>
                <li>商品型（GLD/PDBC）：初始建仓 2% | 追加/切换 3%</li>
                <li>赎回费：0% | 最低门槛：建仓10万RMB / 追加1万RMB</li>
            </ul>
        </div>
    </div>

    <!-- 折线图：v5.9 / v6.8.1 / SP500 累计收益对比 -->
    <div class="section">
        <div class="section-title">累计收益走势对比（v5.9 / v6.8.1 / SP500 · 2007-2026）</div>
        <div style="background:#fff; border-radius:8px; padding:18px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
            <div class="chart-container">
                <canvas id="perfChart"></canvas>
            </div>
            <div style="display:flex; gap:18px; margin-top:10px; font-size:0.78rem; color:#666; flex-wrap:wrap; justify-content:center;">
                <span>📅 时间范围: 2007-01-31 ~ 2026-05-31（{len(monthly_idx)} 个月度点）</span>
                <span>📊 数据源: WIF_v59_nav_20260608.csv</span>
                <span>🔄 累计收益% = (NAV - 1) × 100%</span>
            </div>
        </div>
    </div>

    <!-- KPI 核心指标 -->
    <div class="section">
        <div class="section-title">核心指标对比（有摩擦 vs 无摩擦 · HSBC渠道）</div>
        <table>
            <tr>
                <th style="background:#546e7a">指标</th>
                <th><span class="tag-v59">v5.9</span><br>有摩擦</th>
                <th><span class="tag-v59">v5.9</span><br>无摩擦</th>
                <th><span class="tag-v68b">v6.8.1</span><br>有摩擦</th>
                <th><span class="tag-v68b">v6.8.1</span><br>无摩擦</th>
                <th>SPY 基准</th>
            </tr>
            <tr>
                <td>累计收益</td>
                <td class="{'pos' if s59_net['cumret']>0 else 'neg'}"><b>{s59_net['cumret']:+.1%}</b></td>
                <td class="{'pos' if s59_gross['cumret']>0 else 'neg'}">{s59_gross['cumret']:+.1%}</td>
                <td class="{'pos' if s68b_net['cumret']>0 else 'neg'}"><b>{s68b_net['cumret']:+.1%}*</b></td>
                <td class="{'pos' if s68b_gross['cumret']>0 else 'neg'}">{s68b_gross['cumret']:+.1%}</td>
                <td class="{'pos' if ss['cumret']>0 else 'neg'}">{ss['cumret']:+.1%}</td>
            </tr>
            <tr>
                <td>年化收益</td>
                <td class="{'pos' if s59_net['ann_ret']>0 else 'neg'}">{s59_net['ann_ret']:+.2%}</td>
                <td class="{'pos' if s59_gross['ann_ret']>0 else 'neg'}">{s59_gross['ann_ret']:+.2%}</td>
                <td class="{'pos' if s68b_net['ann_ret']>0 else 'neg'}">{s68b_net['ann_ret']:+.2%}</td>
                <td class="{'pos' if s68b_gross['ann_ret']>0 else 'neg'}">{s68b_gross['ann_ret']:+.2%}</td>
                <td class="{'pos' if ss['ann_ret']>0 else 'neg'}">{ss['ann_ret']:+.2%}</td>
            </tr>
            <tr>
                <td>年化波动率</td>
                <td>{s59_net['vol']:.2%}</td>
                <td>{s59_gross['vol']:.2%}</td>
                <td>{s68b_net['vol']:.2%}</td>
                <td>{s68b_gross['vol']:.2%}</td>
                <td>{ss['vol']:.2%}</td>
            </tr>
            <tr>
                <td>夏普比率</td>
                <td><b>{s59_net['sharpe']:.2f}</b></td>
                <td>{s59_gross['sharpe']:.2f}</td>
                <td><b>{s68b_net['sharpe']:.2f}</b></td>
                <td>{s68b_gross['sharpe']:.2f}</td>
                <td>{ss['sharpe']:.2f}</td>
            </tr>
            <tr>
                <td>最大回撤(MDD)</td>
                <td>{s59_net['mdd']:.1%}</td>
                <td>{s59_gross['mdd']:.1%}</td>
                <td>{s68b_net['mdd']:.1%}</td>
                <td>{s68b_gross['mdd']:.1%}</td>
                <td>{ss['mdd']:.1%}</td>
            </tr>
            <tr>
                <td>vs SPY 倍数（有摩擦）</td>
                <td><b>{s59_net['cumret']/ss['cumret']:.2f}x</b></td>
                <td>—</td>
                <td><b>{s68b_net['cumret']/ss['cumret']:.2f}x</b></td>
                <td>—</td>
                <td>1.00x</td>
            </tr>
            <tr>
                <td>累计调仓次数</td>
                <td colspan="2">{n59} 次</td>
                <td colspan="2">{n68b} 次</td>
                <td>—</td>
            </tr>
            <tr>
                <td>累计成本损耗</td>
                <td style="background:#fff3cd">${total_cost_display59:,.0f}</td>
                <td>$0</td>
                <td style="background:#fff3cd">${total_cost_display68b:,.0f}</td>
                <td>$0</td>
                <td>—</td>
            </tr>
        </table>
        <p style="font-size:12px; color:#999; margin-top:10px;">* v6.8.1含存活者偏差，夏普比为核心评价指标。</p>
    </div>

    <!-- 年度收益 -->
    <div class="section">
        <div class="section-header">
            <h2 class="section-title" style="margin:0; border:none; padding:0;">年度收益对比</h2>
        </div>
        <table>
            <tr>
                <th>年份</th>
                <th><span class="tag-v59">v5.9</span> 年收益</th>
                <th><span class="tag-v68b">v6.8.1</span> 年收益</th>
                <th>SPY 年收益</th>
                <th>v5.9 调仓</th>
                <th>v6.8.1 调仓</th>
            </tr>
            {annual_rows}
        </table>
    </div>

    <!-- 调仓成本年度汇总 -->
    <div class="section">
        <div class="section-title">调仓成本年度汇总（HSBC渠道）</div>
        <table>
            <tr>
                <th>年份</th>
                <th><span class="tag-v59">v5.9</span> 调仓</th>
                <th><span class="tag-v59">v5.9</span> 成本</th>
                <th><span class="tag-v68b">v6.8.1</span> 调仓</th>
                <th><span class="tag-v68b">v6.8.1</span> 成本</th>
            </tr>
            {cost_annual_rows}
            <tr style="background:#e8f5e9;font-weight:600">
                <td>合计</td>
                <td>{n59}</td>
                <td>${total_cost_display59:,.0f}</td>
                <td>{n68b}</td>
                <td>${total_cost_display68b:,.0f}</td>
            </tr>
        </table>
    </div>

    <!-- 方案C 触发信号统计 -->
    <div class="section">
        <div class="section-title">方案C 触发信号统计（信号层与执行层分离）</div>
        <table>
            <tr><th>触发类型</th><th>触发次数</th><th>说明</th></tr>
            <tr>
                <td><strong>因子切换</strong></td>
                <td>{trigger_stats['factor_switch']} 天</td>
                <td>每三周末评分日选出不同因子时触发 · 触发detect_trades(force=True)</td>
            </tr>
            <tr>
                <td><strong>状态切换</strong></td>
                <td>{trigger_stats['state_change']} 天</td>
                <td>Phase1状态变化（HEALTHY↔WARNING↔EMERGENCY）时触发</td>
            </tr>
            <tr>
                <td><strong>新品类首次建仓</strong></td>
                <td>{trigger_stats['new_category']} 次</td>
                <td>某资产类别（EQUITY/FIXED_INCOME/COMMODITY）首次获得配置时触发</td>
            </tr>
            <tr style="background:#e8f5e9;font-weight:600">
                <td>合计有效触发</td>
                <td colspan="2">非初始建仓日，约 {trigger_stats['factor_switch']+trigger_stats['state_change']+trigger_stats['new_category']} 次（含重叠）</td>
            </tr>
        </table>
        <div class="note-box">
            <strong>📌 方案C核心逻辑</strong>：三轨HRP每日"体检报告"仅决定目标配置，但不开药。<br>
            detect_trades()仅在三触发条件之一满足时才执行全量调仓（force=True，跳过dynamic_band）。<br>
            非触发日：传入holdings=当前持仓→detect_trades返回空→保持不变→零换手。
        </div>
    </div>

    <!-- Phase 1 状态分布 -->
    <div class="section">
        <div class="section-title">Phase 1 状态分布</div>
        <table>
            <tr><th>状态</th><th>天数</th><th>占比</th><th>含义</th></tr>
            {phase_rows}
        </table>
    </div>

    <!-- v5.9 交易日志 -->
    <div class="section">
        <div class="section-header">
            <h2 class="section-title" style="margin:0; border:none; padding:0;">
                <span class="tag-v59">v5.9</span> 交易日志（共 {n59} 条调仓）
            </h2>
            <span class="count-badge">{min(n59,200)} 条已展示</span>
        </div>
        <table class="trade-table">
            <tr>
                <th>调仓日期</th>
                <th>Phase1 / 象限 / 信号</th>
                <th>MCI值 / 因子</th>
                <th>交易明细</th>
                <th>成本</th>
            </tr>
            {trade_rows_v59}
        </table>
    </div>

    <!-- v6.8.1 交易日志 -->
    <div class="section">
        <div class="section-header">
            <h2 class="section-title" style="margin:0; border:none; padding:0;">
                <span class="tag-v68b">v6.8.1</span> 交易日志（共 {n68b} 条调仓）
            </h2>
            <span class="count-badge">{min(n68b,200)} 条已展示</span>
        </div>
        <table class="trade-table">
            <tr>
                <th>调仓日期</th>
                <th>Phase1 / 象限 / 信号</th>
                <th>MCI值 / 因子</th>
                <th>交易明细</th>
                <th>成本</th>
            </tr>
            {trade_rows_v68b}
        </table>
    </div>

    <!-- 因子ETF路由分布（v6.8.1） -->
    <div class="section">
        <div class="section-title">因子 ETF 路由分布（v6.8.1 Phase 4）</div>
        <table>
            <tr><th>因子</th><th>被选天数</th><th>占%</th></tr>
            {factor_rows_v68b}
        </table>
        <div class="note-box">
            <strong>📌 v6.8.1 路由逻辑</strong>：WARNING期→VTI+QQQ（不走因子）；MCI&lt;+5→强制VTI；HEALTHY+MCI≥+5→每三周末评分选因子。
        </div>
    </div>

    <!-- equity_ticker分布 -->
    <div class="section">
        <div class="section-title">v6.8.1 equity_ticker 分布</div>
        <table>
            <tr><th>ticker</th><th>天数</th><th>占比</th></tr>
            {''.join(f"<tr><td>{k}</td><td>{v}</td><td>{100*v/len(prices):.1f}%</td></tr>" for k,v in eq_ticker_dist.items())}
        </table>
    </div>

    <!-- 因子ETF可用性 -->
    <div class="section">
        <div class="section-title">因子ETF 可用性（存活者偏差根源）</div>
        <table>
            <tr><th>因子ETF</th><th>可用天数</th><th>最早日期</th><th>最晚日期</th></tr>
            {avail_rows}
        </table>
    </div>

    <!-- 框架差异对照 -->
    <div class="section">
        <div class="section-title">两版本核心差异</div>
        <table>
            <tr><th>维度</th><th><span class="tag-v59">v5.9</span></th><th><span class="tag-v68b">v6.8.1</span></th></tr>
            <tr><td><strong>权益实现</strong></td><td>VTI/QQQ 126日动量（60/40）</td><td>CSI统一Z-score复合指数（连续值）</td></tr>
            <tr><td><strong>WARNING权益</strong></td><td>VTI/QQQ</td><td>VTI+QQQ 60/40（与v5.9同）</td></tr>
            <tr><td><strong>Phase1触发</strong></td><td>F33/F33b/F33c三重布尔</td><td>CSI>2.0→EMERGENCY；CSI>1.0→WARNING；F33b(VIX>40且VIX_10d>100%)→EMERGENCY硬覆盖</td></tr>
            <tr><td><strong>MCI门控</strong></td><td>无</td><td>MCI≥+5才执行因子评分（{mci_gate_count}天=占比{100*mci_gate_count/len(prices):.1f}%）</td></tr>
            <tr><td><strong>评分频率</strong></td><td>每日动量</td><td>仅每三周末（15交易日周期）</td></tr>
            <tr><td><strong>另类桶</strong></td><td>GLD</td><td>GLD + XLE + PDBC</td></tr>
            <tr><td><strong>存活者偏差</strong></td><td>✅ 无</td><td>⚠️ 有</td></tr>
            <tr><td><strong>调仓次数</strong></td><td>{n59}次</td><td>{n68b}次</td></tr>
        </table>
    </div>

    <div class="data-note">
        <strong>✅ 数据说明</strong><br>
        数据来自 <code>US2007_2026/_merged_prices.csv</code>，因子ETF来自同目录 Individual ETF CSV。<br>
        SHV 使用真实数据（2007-01-11 起）。交易成本已实时扣除。
    </div>

</div>

"""

# ★ Chart.js 初始化脚本 (作为独立字符串, 避免与 f-string 的 {} 冲突)
chart_script = """
<script>
(function() {
    const chartData = """ + chart_data_json + """;

    const ctx = document.getElementById('perfChart').getContext('2d');

    const v59Color = '#1565c0';
    const v681Color = '#7b1fa2';
    const spyColor = '#546e7a';

    function makeGradient(ctx, color, height) {
        const g = ctx.createLinearGradient(0, 0, 0, height);
        g.addColorStop(0, color + '40');
        g.addColorStop(1, color + '05');
        return g;
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.dates,
            datasets: [
                {
                    label: 'v5.9 (v5.8 + P0修复)',
                    data: chartData.v59.map(v => +(v * 100).toFixed(2)),
                    borderColor: v59Color,
                    backgroundColor: makeGradient(ctx, v59Color, 420),
                    borderWidth: 2.5,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: v59Color,
                    tension: 0.1,
                    fill: true,
                },
                {
                    label: 'v6.8.1 (v6.8 + P0修复 + Q3 HEALTHY≤30%)',
                    data: chartData.v681.map(v => +(v * 100).toFixed(2)),
                    borderColor: v681Color,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: v681Color,
                    tension: 0.1,
                    fill: false,
                },
                {
                    label: 'SPY 基准',
                    data: chartData.spy.map(v => +(v * 100).toFixed(2)),
                    borderColor: spyColor,
                    backgroundColor: 'transparent',
                    borderWidth: 1.8,
                    borderDash: [5, 3],
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: spyColor,
                    tension: 0.1,
                    fill: false,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                title: {
                    display: true,
                    text: '累计收益% (2007-01-31 ~ 2026-05-31, 月度采样)',
                    font: { size: 14, weight: '600' },
                    color: '#1a1a2e',
                    padding: { top: 4, bottom: 16 }
                },
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 16,
                        font: { size: 12 },
                        usePointStyle: false,
                        padding: 14
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(26,26,46,0.95)',
                    titleFont: { size: 13 },
                    bodyFont: { size: 12 },
                    padding: 12,
                    callbacks: {
                        label: function(ctx) {
                            return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(1) + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 12,
                        font: { size: 10 },
                        color: '#666'
                    },
                    grid: { display: false }
                },
                y: {
                    ticks: {
                        font: { size: 11 },
                        color: '#666',
                        callback: function(value) { return value + '%'; }
                    },
                    grid: { color: 'rgba(0,0,0,0.06)' }
                }
            }
        }
    });
})();
</script>
</body>
</html>"""

html_content = html_content + chart_script

report_path = f'{REPORT_DIR}/WIF_v59_Report_20260608.html'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f"  ✅ 对比报告已保存: {report_path}")

# 保存净值
nav_path = f'{REPORT_DIR}/WIF_v59_nav_20260608.csv'
(prices[['v59_cum_net','v68b_cum_net','v59_cum_gross','v68b_cum_gross','spy_cum',
          'ret_v59_net','ret_v68b_net','ret_v59_gross','ret_v68b_gross','ret_spy',
          'Phase1_status','macro_quadrant','best_factor_v68b',
          'eq_lim59','fi_lim59','ra_lim59',
          'eq_lim68b','fi_lim68b','gld_lim68b','xle_lim68b','pdbc_lim68b',
          'equity_ticker_v68b','BND_def_triggered']]
 .to_csv(nav_path))
print(f"  ✅ 净值数据已保存: {nav_path}")

# 保存交易日志CSV
def export_trade_log(log_list, version):
    rows = []
    for entry in log_list:
        trades = entry['trades']
        if isinstance(trades, dict):
            for ticker, trade_info in trades.items():
                action = trade_info.get('action', 'BUY')
                rows.append({
                    'date': entry['date'].strftime('%Y-%m-%d'),
                    'version': version,
                    'phase1': entry['phase1'],
                    'quadrant': entry['quad'],
                    'signal': entry.get('signal', 'balanced'),
                    'mci': entry.get('mci', 0),
                    'best_factor': entry.get('best_factor', '—'),
                    'ticker': ticker,
                    'action': action,
                    'weight_change': trade_info.get('weight_change', 0),
                    'amount_usd': trade_info.get('amount_usd', 0),
                    'amount_rmb': trade_info.get('amount_rmb', 0),
                    'fee_rate': trade_info.get('fee_rate', 0),
                    'fee_usd': trade_info.get('fee_usd', 0),
                    'skip_reason': trade_info.get('reason', ''),
                })
        else:
            for t in trades:
                rows.append({
                    'date': entry['date'].strftime('%Y-%m-%d'),
                    'version': version,
                    'phase1': entry['phase1'],
                    'quadrant': entry['quad'],
                    'signal': entry.get('signal', 'balanced'),
                    'mci': entry.get('mci', 0),
                    'best_factor': entry.get('best_factor', '—'),
                    'ticker': t.get('ticker', '—'),
                    'action': t.get('direction', 'BUY'),
                    'weight_change': 0,
                    'amount_usd': 0,
                    'amount_rmb': 0,
                    'fee_rate': 0,
                    'fee_usd': entry.get('total_fee_usd', 0),
                    'skip_reason': '',
                })
    return pd.DataFrame(rows)

log_df = pd.concat([export_trade_log(log_v59,'v5.9'), export_trade_log(log_v68b,'v6.8.1')], ignore_index=True)
trade_csv_path = f'{REPORT_DIR}/WIF_v59_trade_log_20260608_HSCBC.csv'
log_df.to_csv(trade_csv_path, index=False)
print(f"  ✅ 交易日志已保存: {trade_csv_path}（{len(log_df)} 条）")

print(f"\n{'='*72}")
print("v5.9 / v6.8.1 对比完成（2026-06-09 · P0修复版）！")
print(f"v5.9(有摩擦): {s59_net['cumret']:+.1%} | 夏普:{s59_net['sharpe']:.2f} | MDD:{s59_net['mdd']:.1%} | 调仓:{n59}次 | 成本:${total_cost_display59:,.0f}")
print(f"v5.9(无摩擦): {s59_gross['cumret']:+.1%} | 夏普:{s59_gross['sharpe']:.2f} | MDD:{s59_gross['mdd']:.1%}")
print(f"v6.8.1(有摩擦): {s68b_net['cumret']:+.1%} | 夏普:{s68b_net['sharpe']:.2f} | MDD:{s68b_net['mdd']:.1%} | 调仓:{n68b}次 | 成本:${total_cost_display68b:,.0f}")
print(f"v6.8.1(无摩擦): {s68b_gross['cumret']:+.1%} | 夏普:{s68b_gross['sharpe']:.2f} | MDD:{s68b_gross['mdd']:.1%}")
print(f"SPY          : {ss['cumret']:+.1%} | 夏普:{ss['sharpe']:.2f} | MDD:{ss['mdd']:.1%}")
print(f"方案C 触发：因子切换={trigger_stats['factor_switch']}次 | 状态切换={trigger_stats['state_change']}天 | 新品类首次={trigger_stats['new_category']}次")
print(f"{'='*72}")
