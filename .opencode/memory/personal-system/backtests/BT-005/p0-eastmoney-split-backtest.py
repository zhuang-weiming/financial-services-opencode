#!/usr/bin/env python3
"""
P0 Priority Backtest: 东财分拆验证 — BT-003 是否存在东财偏差

验证 BT-003（券商PB vs 成交量）中，东方财富(300059)作为互联网券商
混入传统券商样本是否扭曲了PB-成交量关系。

Author: backtest-builder (subagent)
Date: 2026-07-29
"""

import akshare as ak
import pandas as pd
import numpy as np
from scipy import stats
import warnings
import json
import os
warnings.filterwarnings('ignore')

print("=" * 80)
print("P0 回测：东财分拆验证 — BT-003 是否存在东财偏差")
print("=" * 80)

# ============================================================
# 1. 数据获取
# ============================================================

# 券商列表（代码, 名称, 市场标识）
BROKERS = {
    "600030.SH": "中信证券",
    "601688.SH": "华泰证券",
    "601881.SH": "中国银河",
    "600999.SH": "招商证券",
    "000776.SZ": "广发证券",
    "601211.SH": "国泰君安",
    "600837.SH": "海通证券",
    "300059.SZ": "东方财富",
}

TRADITIONAL_BROKERS = {k: v for k, v in BROKERS.items() if k != "300059.SZ"}

# ---- 1a. 获取各券商月度 PB ----
print("\n[1a] 获取各券商月度 PB 数据...")

def get_bps_data(symbol):
    """获取个股BPS（每股净资产）数据"""
    try:
        df = ak.stock_financial_analysis_indicator_em(symbol=symbol, indicator='按报告期')
        if 'REPORT_DATE' in df.columns and 'BPS' in df.columns:
            result = df[['REPORT_DATE', 'BPS']].copy()
            result['REPORT_DATE'] = pd.to_datetime(result['REPORT_DATE'])
            result['BPS'] = pd.to_numeric(result['BPS'], errors='coerce')
            result = result.sort_values('REPORT_DATE')
            return result
    except Exception as e:
        print(f"  ⚠️ {symbol} BPS 获取失败: {e}")
    return pd.DataFrame()

def get_monthly_price(symbol_code):
    """获取月度价格数据"""
    try:
        df = ak.stock_zh_a_hist(symbol=symbol_code, period='monthly', 
                                start_date='20091201', end_date='20260731')
        if '日期' in df.columns and '收盘' in df.columns:
            df = df[['日期', '收盘']].copy()
            df['日期'] = pd.to_datetime(df['日期'])
            df['收盘'] = pd.to_numeric(df['收盘'], errors='coerce')
            df = df.rename(columns={'收盘': 'close'})
            df = df.sort_values('日期')
            return df
    except Exception as e:
        print(f"  ⚠️ {symbol_code} 月度价格获取失败: {e}")
    return pd.DataFrame()

def compute_monthly_pb(symbol_with_suffix):
    """计算月度PB = 月末收盘价 / 最新BPS"""
    symbol_code = symbol_with_suffix.split('.')[0]
    name = BROKERS.get(symbol_with_suffix, symbol_with_suffix)
    
    # 获取月度价格
    price_df = get_monthly_price(symbol_code)
    if price_df.empty:
        print(f"  ❌ {name}({symbol_with_suffix}): 无法获取价格数据")
        return pd.DataFrame()
    
    # 获取BPS数据
    bps_df = get_bps_data(symbol_with_suffix)
    if bps_df.empty:
        print(f"  ❌ {name}({symbol_with_suffix}): 无法获取BPS数据")
        return pd.DataFrame()
    
    # 将BPS forward-fill 到月度频率
    # 对每个月末，使用该日期之前的最新BPS
    price_df = price_df.copy()
    price_df['month_end'] = price_df['日期']
    
    # 合并：使用BPS的最新值
    merged = []
    for _, row in price_df.iterrows():
        dt = row['日期']
        # 找到该日期之前的最新BPS
        available_bps = bps_df[bps_df['REPORT_DATE'] <= dt]
        if available_bps.empty:
            continue
        latest_bps = available_bps.iloc[-1]['BPS']
        if pd.isna(latest_bps) or latest_bps <= 0:
            continue
        pb = row['close'] / latest_bps
        merged.append({
            'date': dt,
            'price': row['close'],
            'bps': latest_bps,
            'pb': pb
        })
    
    result = pd.DataFrame(merged)
    if result.empty:
        print(f"  ❌ {name}({symbol_with_suffix}): 合并后无数据")
    else:
        print(f"  ✅ {name}({symbol_with_suffix}): {len(result)} 个月度PB数据 ({result['date'].min().strftime('%Y-%m')} ~ {result['date'].max().strftime('%Y-%m')})")
    return result

# 获取所有股票的月度PB
all_pb_data = {}
for sym, name in BROKERS.items():
    print(f"\n  获取 {name}({sym})...")
    df = compute_monthly_pb(sym)
    if not df.empty:
        all_pb_data[sym] = df

print(f"\n  成功获取 {len(all_pb_data)}/{len(BROKERS)} 只股票的PB数据")

# ---- 1b. 获取全市场月度成交额 ----
print("\n[1b] 获取全市场月度成交额...")

market_volume = pd.DataFrame()
try:
    mkt = ak.macro_china_stock_market_cap()
    # 解析日期: "2026年06月份" -> use month start
    def parse_china_month(s):
        s = s.replace('年', '-').replace('月份', '').replace('月', '')
        return pd.to_datetime(s + '-01', format='%Y-%m-%d', errors='coerce')
    
    mkt['数据日期'] = mkt['数据日期'].apply(parse_china_month)
    
    # 全市场成交额 = 上海 + 深圳
    mkt['成交金额-上海'] = pd.to_numeric(mkt['成交金额-上海'], errors='coerce')
    mkt['成交金额-深圳'] = pd.to_numeric(mkt['成交金额-深圳'], errors='coerce')
    mkt['total_turnover'] = mkt['成交金额-上海'] + mkt['成交金额-深圳']
    
    market_volume = mkt[['数据日期', 'total_turnover']].copy()
    market_volume = market_volume.rename(columns={'数据日期': 'date'})
    market_volume = market_volume.sort_values('date').dropna()
    
    # 将日期移至月末（与PB数据对齐）
    market_volume['date'] = market_volume['date'] + pd.offsets.MonthEnd(1)
    
    print(f"  ✅ 全市场月度成交额: {len(market_volume)} 个月 ({market_volume['date'].min().strftime('%Y-%m')} ~ {market_volume['date'].max().strftime('%Y-%m')})")
    print(f"  首行: {market_volume.head(1).to_string()}")
except Exception as e:
    print(f"  ❌ 全市场成交额获取失败: {e}")
    import traceback
    traceback.print_exc()

# ---- 1c. 获取创业板月度成交额 ----
print("\n[1c] 获取创业板月度成交额...")

gem_volume = pd.DataFrame()
try:
    gem_daily = ak.stock_zh_index_daily_em(symbol='sz399006', start_date='20091201', end_date='20260731')
    gem_daily['date'] = pd.to_datetime(gem_daily['date'])
    gem_daily['amount'] = pd.to_numeric(gem_daily['amount'], errors='coerce')
    
    # 按月汇总
    gem_daily['month'] = gem_daily['date'].dt.to_period('M')
    gem_monthly = gem_daily.groupby('month').agg({
        'amount': 'sum',
        'date': 'last'  # 使用月末日期
    }).reset_index()
    gem_monthly = gem_monthly.rename(columns={'date': 'last_trade_date', 'amount': 'gem_turnover'})
    # 用 month end 日期，与PB对齐
    gem_monthly['date'] = gem_monthly['month'].dt.to_timestamp().dt.to_period('M').dt.to_timestamp() + pd.offsets.MonthEnd(1)
    
    gem_volume = gem_monthly[['date', 'gem_turnover']].sort_values('date')
    
    print(f"  ✅ 创业板月度成交额: {len(gem_volume)} 个月 ({gem_volume['date'].min().strftime('%Y-%m')} ~ {gem_volume['date'].max().strftime('%Y-%m')})")
except Exception as e:
    print(f"  ❌ 创业板成交额获取失败: {e}")

# ============================================================
# 2. 数据对齐与合并
# ============================================================

print("\n[2] 数据对齐与合并...")

# 构建三个PB序列
print("\n  构建7家传统券商平均PB...")
trad_pb_dfs = []
for sym in TRADITIONAL_BROKERS:
    if sym in all_pb_data:
        df = all_pb_data[sym][['date', 'pb']].copy()
        df = df.rename(columns={'pb': f'pb_{sym}'})
        trad_pb_dfs.append(df)
        print(f"    {TRADITIONAL_BROKERS[sym]}({sym}): {len(df)} 条")

# 合并传统券商PB
if trad_pb_dfs:
    trad_pb = trad_pb_dfs[0]
    for df in trad_pb_dfs[1:]:
        trad_pb = trad_pb.merge(df, on='date', how='outer')
    
    # 计算平均PB
    pb_cols = [c for c in trad_pb.columns if c.startswith('pb_')]
    print(f"  参与平均的PB列: {pb_cols} ({len(pb_cols)} 只)")
    trad_pb['trad_avg_pb'] = trad_pb[pb_cols].mean(axis=1)
    trad_pb = trad_pb.sort_values('date')
    print(f"  ✅ 传统券商平均PB: {len(trad_pb)} 条 ({trad_pb['date'].min().strftime('%Y-%m')} ~ {trad_pb['date'].max().strftime('%Y-%m')})")
else:
    print("  ❌ 无传统券商数据")
    trad_pb = pd.DataFrame()

# 东财PB
eastmoney_pb = all_pb_data.get('300059.SZ', pd.DataFrame())
if not eastmoney_pb.empty:
    eastmoney_pb = eastmoney_pb[['date', 'pb']].rename(columns={'pb': 'em_pb'})
    print(f"  ✅ 东财PB: {len(eastmoney_pb)} 条")

# 合并所有数据
print("\n  合并数据集...")
merged = trad_pb[['date', 'trad_avg_pb']].copy() if not trad_pb.empty else pd.DataFrame()

if not eastmoney_pb.empty and not merged.empty:
    merged = merged.merge(eastmoney_pb, on='date', how='outer')
elif not eastmoney_pb.empty:
    merged = eastmoney_pb.copy()

if not market_volume.empty and not merged.empty:
    merged = merged.merge(market_volume, on='date', how='left')

if not gem_volume.empty and not merged.empty:
    merged = merged.merge(gem_volume, on='date', how='left')

merged = merged.sort_values('date').dropna(subset=['date'])
print(f"  ✅ 合并数据集: {len(merged)} 行 ({merged['date'].min().strftime('%Y-%m')} ~ {merged['date'].max().strftime('%Y-%m')})")

# 显示各列非空计数
print("\n  数据完整性:")
for col in merged.columns:
    non_null = merged[col].notna().sum()
    print(f"    {col}: {non_null}/{len(merged)} ({non_null/len(merged)*100:.1f}%)")

# ============================================================
# 3. 回测执行
# ============================================================

print("\n" + "=" * 80)
print("3. 回测执行")
print("=" * 80)

def run_pearson_correlation(data, x_col, y_col, label=""):
    """运行Pearson相关分析"""
    cols = [x_col, y_col]
    if 'date' in data.columns:
        cols = ['date'] + cols
    valid = data[cols].dropna()
    if len(valid) < 5:
        return {"n": 0, "r": None, "p": None, "r2": None, "label": label}
    
    x = valid[x_col].values
    y = valid[y_col].values
    
    # Pearson相关
    r, p_value = stats.pearsonr(x, y)
    r2 = r ** 2
    
    # Spearman秩相关（稳健性检验）
    sp, _ = stats.spearmanr(x, y)
    
    # 线性回归斜率
    slope, intercept, _, _, _ = stats.linregress(x, y)
    
    return {
        "n": len(valid),
        "r": round(r, 4),
        "p": round(p_value, 6),
        "r2": round(r2, 4),
        "spearman_r": round(sp, 4),
        "slope": round(slope, 8),
        "intercept": round(intercept, 4),
        "start": valid['date'].min().strftime('%Y-%m'),
        "end": valid['date'].max().strftime('%Y-%m'),
        "label": label,
        "significant": p_value < 0.05
    }

def print_corr_result(result, indent="  "):
    """打印相关结果"""
    if result['n'] == 0:
        print(f"{indent}❌ 无有效数据")
        return
    sig = "***" if result['p'] < 0.001 else "**" if result['p'] < 0.01 else "*" if result['p'] < 0.05 else ""
    print(f"{indent}📊 {result['label']}")
    print(f"{indent}  样本量: n={result['n']}")
    print(f"{indent}  Pearson r = {result['r']:.4f}{sig},  p = {result['p']:.6f}")
    print(f"{indent}  R² = {result['r2']:.4f}")
    print(f"{indent}  Spearman ρ = {result['spearman_r']:.4f}")
    print(f"{indent}  回归斜率 = {result['slope']:.8f}")
    print(f"{indent}  {'✅ 显著' if result['significant'] else '❌ 不显著'} (α=0.05)")

# 定义时间段
periods = {
    "全样本": ("2010-01", "2026-06"),
    "2015年前": ("2010-01", "2014-12"),
    "2015-2020": ("2015-01", "2020-12"),
    "2020-2026": ("2021-01", "2026-06"),
}

# 定义回测方案
scenarios = [
    {
        "name": "回测A: 7家传统券商平均PB vs 全市场成交量",
        "id": "A",
        "x": "total_turnover",
        "y": "trad_avg_pb",
        "desc": "剔除东财后的关系"
    },
    {
        "name": "回测B: 东财PB vs 全市场成交量",
        "id": "B",
        "x": "total_turnover",
        "y": "em_pb",
        "desc": "东财单独 vs 全市场"
    },
    {
        "name": "回测C: 东财PB vs 创业板成交量",
        "id": "C",
        "x": "gem_turnover",
        "y": "em_pb",
        "desc": "东财单独 vs 创业板（东财收入更相关）"
    },
]

# BT-003 原始结果对比
bt003_original = "全样本 Pearson r = -0.13, p = 0.15, R² = 0.007"

results_summary = []

for sc in scenarios:
    print(f"\n--- {sc['name']} ---")
    
    for period_name, (start, end) in periods.items():
        # 筛选时间段
        mask = (merged['date'] >= start) & (merged['date'] <= end)
        subset = merged[mask].copy()
        
        if subset.empty or subset[sc['x']].isna().all() or subset[sc['y']].isna().all():
            print(f"  [{period_name}] 数据不足，跳过")
            continue
        
        result = run_pearson_correlation(
            subset, sc['x'], sc['y'],
            label=f"{sc['name']} | {period_name}"
        )
        result['period'] = period_name
        result['scenario'] = sc['id']
        result['scenario_name'] = sc['name']
        result['start'] = start
        result['end'] = end
        results_summary.append(result)
        print_corr_result(result)

# ============================================================
# 4. 补充分析：东财PB vs 传统券商PB走势对比
# ============================================================

print("\n" + "=" * 80)
print("4. 补充分析：东财PB vs 传统券商PB走势对比")
print("=" * 80)

# 对比东财和传统PB序列
pb_compare = merged[['date', 'trad_avg_pb', 'em_pb']].dropna()
if not pb_compare.empty:
    # 描述统计
    print(f"\n  描述统计 (n={len(pb_compare)}):")
    for col, label in [('trad_avg_pb', '传统券商平均PB'), ('em_pb', '东财PB')]:
        print(f"    {label}: 均值={pb_compare[col].mean():.2f}, "
              f"中位数={pb_compare[col].median():.2f}, "
              f"标准差={pb_compare[col].std():.2f}, "
              f"最小={pb_compare[col].min():.2f}, "
              f"最大={pb_compare[col].max():.2f}")
    
    # 两者的相关性
    corr_result = run_pearson_correlation(pb_compare, 'trad_avg_pb', 'em_pb',
                                          label="传统券商PB vs 东财PB")
    print_corr_result(corr_result)
    
    # 溢价分析：东财PB相对于传统PB的溢价
    pb_compare['em_premium'] = pb_compare['em_pb'] / pb_compare['trad_avg_pb'] - 1
    print(f"\n  东财相对传统券商PB溢价:")
    print(f"    均值: {pb_compare['em_premium'].mean()*100:.1f}%")
    print(f"    中位数: {pb_compare['em_premium'].median()*100:.1f}%")
    print(f"    标准差: {pb_compare['em_premium'].std()*100:.1f}%")
    print(f"    最小: {pb_compare['em_premium'].min()*100:.1f}%")
    print(f"    最大: {pb_compare['em_premium'].max()*100:.1f}%")
    
    # 分时期溢价
    for period_name, (start, end) in periods.items():
        mask = (pb_compare['date'] >= start) & (pb_compare['date'] <= end)
        subset = pb_compare[mask]
        if len(subset) > 3:
            premium = subset['em_premium'].mean() * 100
            print(f"    [{period_name}] 平均溢价: {premium:.1f}% (n={len(subset)})")

# ============================================================
# 5. 各券商PB差异分析
# ============================================================

print("\n" + "=" * 80)
print("5. 各券商PB差异分析")
print("=" * 80)

# 计算各券商在全样本期内的平均PB
all_broker_pbs = []
for sym, name in BROKERS.items():
    if sym in all_pb_data:
        df = all_pb_data[sym]
        avg_pb = df['pb'].mean()
        med_pb = df['pb'].median()
        std_pb = df['pb'].std()
        # 与全市场成交量的相关
        merged_pb = df[['date', 'pb']].merge(market_volume, on='date', how='inner').dropna()
        r, p = stats.pearsonr(merged_pb['pb'], merged_pb['total_turnover']) if len(merged_pb) > 5 else (None, None)
        all_broker_pbs.append({
            'symbol': sym,
            'name': name,
            'avg_pb': round(avg_pb, 2),
            'med_pb': round(med_pb, 2),
            'std_pb': round(std_pb, 2),
            'n_months': len(df),
            'pb_vol_r': round(r, 4) if r else None,
            'pb_vol_p': round(p, 6) if p else None,
        })

if all_broker_pbs:
    broker_df = pd.DataFrame(all_broker_pbs)
    broker_df = broker_df.sort_values('avg_pb', ascending=False)
    print("\n  各券商PB vs 成交量相关系数:")
    print(f"  {'券商':<12} {'平均PB':<10} {'中位PB':<10} {'PB标准差':<10} {'PB-Vol r':<12} {'p值':<10} {'月数':<6}")
    print(f"  {'-'*60}")
    for _, row in broker_df.iterrows():
        r_str = f"{row['pb_vol_r']:.4f}" if row['pb_vol_r'] else 'N/A'
        p_str = f"{row['pb_vol_p']:.4f}" if row['pb_vol_p'] else 'N/A'
        sig = "*" if row['pb_vol_p'] is not None and row['pb_vol_p'] < 0.05 else ""
        print(f"  {row['name']:<8} {row['avg_pb']:<10.2f} {row['med_pb']:<10.2f} {row['std_pb']:<10.2f} {r_str+sig:<12} {p_str:<10} {row['n_months']:<6}")

# ============================================================
# 6. 回答核心问题
# ============================================================

print("\n" + "=" * 80)
print("6. 核心问题回答")
print("=" * 80)

# 提取关键结果
results_df = pd.DataFrame(results_summary)

print(f"\n  关键结果表格:")
print(f"  {'回测':<8} {'时段':<14} {'n':<6} {'Pearson r':<12} {'R²':<8} {'p值':<10} {'Significant':<12}")
print(f"  {'-'*70}")

for _, r in results_df.iterrows():
    sig = "✅" if r['significant'] else "❌"
    r_str = f"{r['r']:.4f}" if r['r'] else "N/A"
    r2_str = f"{r['r2']:.4f}" if r['r2'] else "N/A"
    p_str = f"{r['p']:.6f}" if r['p'] else "N/A"
    print(f"  {r['scenario']+' '+r['scenario_name'][:20]:<28} {r['period']:<10} {r['n']:<6} {r_str:<12} {r2_str:<8} {p_str:<10} {sig:<12}")

# 与BT-003原始结果对比
print(f"\n  BT-003 原始结果: r = -0.13 (p=0.15), R² = 0.007")

# 核心结论
print("\n")
print("  ┌─────────────────────────────────────────────────────────────────┐")
print("  │                     核 心 结 论                                │")
print("  └─────────────────────────────────────────────────────────────────┘")

# 结论1: 东财是否扭曲
trad_full = [r for r in results_summary if r['scenario'] == 'A' and r['period'] == '全样本']
em_full = [r for r in results_summary if r['scenario'] == 'B' and r['period'] == '全样本']

if trad_full and em_full:
    trad_r = trad_full[0]['r']
    em_r = em_full[0]['r']
    print(f"\n  ① 东财是否扭曲BT-003结果?")
    print(f"     传统7家 PB-全市场成交量 r={trad_r:.4f}")
    print(f"     东财单只 PB-全市场成交量 r={em_r:.4f}")
    if abs(em_r) > abs(trad_r):
        print(f"     东财的r绝对值({abs(em_r):.4f})大于传统券商({abs(trad_r):.4f})，说明东财确实有更强(或更不同)的PB-成交量关系")
        if trad_r > -0.13:
            print(f"     传统券商 r={trad_r:.4f} 比 BT-003 的 r=-0.13 更接近0，说明东财混入拉低了相关系数")
        else:
            print(f"     传统券商 r={trad_r:.4f} 比 BT-003 的 r=-0.13 更负，说明东财混入实际上拉高了相关系数")
    else:
        print(f"     东财的r绝对值({abs(em_r):.4f})小于传统券商({abs(trad_r):.4f})，东财的影响较小")

# 结论2: 剔除后关系变化
if trad_full:
    print(f"\n  ② 剔除东财后，传统券商PB-成交量关系是否更弱?")
    trad_r_val = trad_full[0]['r']
    if abs(trad_r_val) < 0.13:
        print(f"     是。剔除东财后 r={trad_r_val:.4f}，绝对值小于 BT-003 的 r=-0.13")
        print(f"     说明东财混入使得原本就很弱的负相关看起来更强（绝对值更大）")
    elif abs(trad_r_val) >= 0.13:
        print(f"     否。剔除东财后 r={trad_r_val:.4f}，绝对值大于等于 BT-003 的 r=-0.13")
        print(f"     说明东财混入实际上弱化了传统券商的负相关关系")

# 结论3: 东财是否应单独建模
if em_full:
    em_r_val = em_full[0]['r']
    print(f"\n  ③ 东财的PB行为是否应该被单独建模?")
    print(f"     东财PB-全市场成交量 r={em_r_val:.4f}")
    
    # 检查东财是否与传统券商PB走势不同
    if not pb_compare.empty:
        pb_r = corr_result['r']
        print(f"     东财PB vs 传统券商PB的相关性: r={pb_r:.4f}")
        if pb_r < 0.7:
            print(f"     ✅ 是。东财PB与传统券商PB相关性仅r={pb_r:.4f} (<0.7)，行为显著不同")
        else:
            print(f"     ❌ 否。东财PB与传统券商PB相关性r={pb_r:.4f} (>=0.7)，走势高度一致")
    
    # 检查东财PB的平均溢价
    if 'em_premium' in pb_compare.columns:
        avg_premium = pb_compare['em_premium'].mean() * 100
        print(f"     东财相对传统券商的平均PB溢价: {avg_premium:.1f}%")
        if avg_premium > 30:
            print(f"     ✅ 是。溢价{avg_premium:.1f}%>30%，东财估值逻辑完全不同")
        elif avg_premium > 10:
            print(f"     ⚠️ 部分需要。溢价{avg_premium:.1f}%，高于传统但非天壤之别")
        else:
            print(f"     ❌ 否。溢价{avg_premium:.1f}%<10%，估值水平接近")

# ============================================================
# 7. 保存结果
# ============================================================

print("\n\n[7] 保存结果...")

output_dir = "/Users/weimingzhuang/Documents/source_code/financial-services-opencode/out/swarm-analysis-20260729"

# 保存CSV
merged.to_csv(f"{output_dir}/eastmoney_split_data.csv", index=False, encoding='utf-8-sig')
print(f"  ✅ 数据保存至: eastmoney_split_data.csv")

# 保存结果摘要JSON
results_json = []
for r in results_summary:
    entry = {k: v for k, v in r.items() if k not in ['scenario_name']}
    entry['r'] = entry['r'] if entry['r'] is not None else None
    results_json.append(entry)

with open(f"{output_dir}/eastmoney_split_results.json", 'w') as f:
    json.dump(results_json, f, indent=2, default=str)
print(f"  ✅ 结果保存至: eastmoney_split_results.json")

# 保存各券商PB分析
if all_broker_pbs:
    broker_df.to_csv(f"{output_dir}/broker_pb_analysis.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ 各券商PB分析保存至: broker_pb_analysis.csv")

print("\n" + "=" * 80)
print("回测完成")
print("=" * 80)
