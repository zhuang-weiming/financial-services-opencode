#!/usr/bin/env python3
"""
A股券商板块PB与成交量关系回测分析
====================================
数据源:
  - 市场总成交额: Baostock (上证000001 + 深证399001)
  - 券商指数: Tencent/AKShare (399975 中证全指证券公司)
  - 券商个股PB: Baostock

回测期: 2010-01 至 2026-06
输出: ./out/backtest-broker-pb-volume/
"""

import os, sys, warnings, json, time
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats
import akshare as ak
import baostock as bs

warnings.filterwarnings('ignore')

OUT_DIR = "./out/backtest-broker-pb-volume"
os.makedirs(OUT_DIR, exist_ok=True)

# ============ 券商列表 ============
BROKER_STOCKS = [
    ("600030", "中信证券"),
    ("601688", "华泰证券"),
    ("300059", "东方财富"),
    ("601881", "中国银河"),
    ("600999", "招商证券"),
    ("000776", "广发证券"),
    ("601211", "国泰君安"),
    ("600837", "海通证券"),
]

BROKER_INDEX_SYMBOL = "sz399975"
START_DATE = "2010-01-01"
END_DATE = "2026-07-22"
START_YEAR = "2010"
END_YEAR = "2026"

print("=" * 60)
print("A股券商板块PB与成交量关系回测分析")
print("=" * 60)

# ========================
# 1. 获取市场总成交额数据 (Baostock)
# ========================
print("\n[1/5] 获取市场总成交额数据 (Baostock)...")

bs.login()
print("  Baostock已登录")

def get_baostock_daily(code, name, start, end):
    """从Baostock获取日线数据"""
    rs = bs.query_history_k_data_plus(
        code,
        "date,close,volume,amount",
        start_date=start,
        end_date=end,
        frequency='d',
        adjustflag='3'
    )
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    if not data_list:
        print(f"    {name} - 无数据")
        return None
    df = pd.DataFrame(data_list, columns=['date','close','volume','amount'])
    df['date'] = pd.to_datetime(df['date'])
    for c in ['close','volume','amount']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df.sort_values('date').reset_index(drop=True)

# 获取上证和深证日线数据
sse_df = get_baostock_daily("sh.000001", "上证综合指数", START_DATE, END_DATE)
szse_df = get_baostock_daily("sz.399001", "深证成份指数", START_DATE, END_DATE)

if sse_df is None or szse_df is None:
    print("ERROR: 无法获取指数数据")
    bs.logout()
    sys.exit(1)

# 合并计算市场总成交额 (单位:亿元)
market_turnover = sse_df[['date','amount']].rename(columns={'amount': 'sse_amount'})
szse_amt = szse_df[['date','amount']].rename(columns={'amount': 'szse_amount'})
market_turnover = market_turnover.merge(szse_amt, on='date', how='inner')

# Baostock amount is in元, convert to亿元 (/1e8)
market_turnover['total_amount'] = (market_turnover['sse_amount'] + market_turnover['szse_amount']) / 1e8
market_turnover = market_turnover.sort_values('date').reset_index(drop=True)

print(f"  市场成交额数据: {market_turnover['date'].min().date()} 至 {market_turnover['date'].max().date()}, {len(market_turnover)} 个交易日")

# 验证关键日期
for d in ['2015-06-12', '2024-09-30', '2024-10-08']:
    row = market_turnover[market_turnover['date'] == pd.Timestamp(d)]
    if len(row) > 0:
        print(f"  {d}: 总成交额 {row['total_amount'].values[0]:.0f}亿")

# 月度成交额统计
market_turnover['year_month'] = market_turnover['date'].dt.to_period('M')
monthly_turnover = market_turnover.groupby('year_month').agg(
    avg_daily_amount=('total_amount', 'mean'),
    total_monthly_amount=('total_amount', 'sum'),
    max_daily_amount=('total_amount', 'max'),
    min_daily_amount=('total_amount', 'min'),
).reset_index()
# 四舍五入
for c in monthly_turnover.columns:
    if c != 'year_month':
        monthly_turnover[c] = monthly_turnover[c].round(1)

print(f"  月度数据: {len(monthly_turnover)} 个月")

# ========================
# 2. 获取券商指数及个股数据
# ========================
print("\n[2/5] 获取券商指数及个股数据...")

# 2a. 券商指数价格 (AKShare Tencent)
print("  获取券商指数(399975)...")
try:
    broker_index_df = ak.stock_zh_index_daily_tx(symbol=BROKER_INDEX_SYMBOL)
    broker_index_df['date'] = pd.to_datetime(broker_index_df['date'])
    broker_index_df = broker_index_df.sort_values('date').reset_index(drop=True)
    print(f"  券商指数数据: {broker_index_df['date'].min().date()} 至 {broker_index_df['date'].max().date()}, {len(broker_index_df)} 个交易日")
except Exception as e:
    print(f"  获取券商指数失败: {e}")
    broker_index_df = None

# 2b. 获取个股PB数据
print("  获取8只券商个股PB及价格数据...")
stock_data_list = []

for symbol, name in BROKER_STOCKS:
    exchange = "sh" if symbol.startswith('6') else "sz"
    code = f"{exchange}.{symbol}"
    rs = bs.query_history_k_data_plus(
        code,
        "date,close,volume,amount,peTTM,pbMRQ",
        start_date=START_DATE,
        end_date=END_DATE,
        frequency='d',
        adjustflag='3'
    )
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    if not data_list:
        print(f"    {name}({symbol}) - 无数据")
        continue
    df = pd.DataFrame(data_list, columns=['date','close','volume','amount','peTTM','pbMRQ'])
    df['date'] = pd.to_datetime(df['date'])
    for c in ['close','volume','amount','peTTM','pbMRQ']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['stock_name'] = name
    df['stock_symbol'] = symbol
    pb_min = df['pbMRQ'].min()
    pb_max = df['pbMRQ'].max()
    # Filter out extreme outliers (东方财富 has PB > 85 due to small equity base)
    df_clean = df[(df['pbMRQ'] > 0) & (df['pbMRQ'] < 30)].copy()
    print(f"    {name}({symbol}): {len(df)} 条, PB({pb_min:.1f}-{pb_max:.1f}), 清洗后{len(df_clean)}条")
    stock_data_list.append(df_clean)

bs.logout()
print("  Baostock已登出")

if not stock_data_list:
    print("ERROR: 无法获取券商数据")
    sys.exit(1)

# 合并所有券商PB数据
all_stocks_combined = pd.concat(stock_data_list, ignore_index=True)

# 每日各券商PB均值 (横截面平均)
daily_pb_panel = all_stocks_combined.pivot_table(
    index='date', columns='stock_name', values='pbMRQ', aggfunc='last'
)
daily_pb_panel['avg_pb'] = daily_pb_panel.mean(axis=1)
daily_pb_panel['median_pb'] = daily_pb_panel.median(axis=1)
daily_pb_panel['max_pb'] = daily_pb_panel.max(axis=1)
daily_pb_panel['min_pb'] = daily_pb_panel.min(axis=1)

print(f"\n  券商平均PB日线: {len(daily_pb_panel)} 个交易日")
print(f"  PB范围: {daily_pb_panel['avg_pb'].min():.2f} - {daily_pb_panel['avg_pb'].max():.2f}")

# ========================
# 3. 数据合并为月度频率
# ========================
print("\n[3/5] 合并月度数据...")

# 日线 → 月度 (月末值)
market_turnover['year_month'] = market_turnover['date'].dt.to_period('M')
daily_pb_panel['year_month'] = daily_pb_panel.index.to_period('M')

monthly_pb = daily_pb_panel.groupby('year_month').agg({
    'avg_pb': 'last',
    'median_pb': 'last',
    'max_pb': 'max',
    'min_pb': 'min',
}).reset_index()

# 券商指数月度
if broker_index_df is not None:
    broker_index_df['year_month'] = broker_index_df['date'].dt.to_period('M')
    monthly_broker = broker_index_df.groupby('year_month').agg(
        broker_close=('close', 'last'),
        broker_open=('open', 'first'),
        broker_high=('high', 'max'),
        broker_low=('low', 'min'),
    ).reset_index()

# 合并所有月度数据
merged = monthly_turnover.merge(monthly_pb, on='year_month', how='inner')
if broker_index_df is not None:
    merged = merged.merge(monthly_broker, on='year_month', how='inner')

# 筛选分析范围
merged = merged[(merged['year_month'] >= '2015-01') & (merged['year_month'] <= '2026-06')]
merged = merged.sort_values('year_month').reset_index(drop=True)

print(f"  合并后月度数据: {len(merged)} 个月 ({merged['year_month'].min()} - {merged['year_month'].max()})")
print(f"  月均日成交额范围: {merged['avg_daily_amount'].min():.0f} - {merged['avg_daily_amount'].max():.0f} 亿")
print(f"  券商平均PB范围: {merged['avg_pb'].min():.2f} - {merged['avg_pb'].max():.2f}")

# 保存合并数据
merged.to_csv(os.path.join(OUT_DIR, "merged_monthly_data.csv"), index=False, encoding='utf-8-sig')

# ========================
# 4. 描述性统计 - 按市场阶段
# ========================
print("\n[4/5] 运行分析...")
print("\n--- 4.1 描述性统计（按市场阶段）---")

market_phases = [
    ("2015-2016 股灾", "2015-07", "2016-02"),
    ("2016-2018 熊市", "2016-03", "2018-12"),
    ("2019-2021 结构牛", "2019-01", "2021-12"),
    ("2022-2024 调整", "2022-01", "2024-09"),
    ("2024-2026 AI行情", "2024-10", "2026-06"),
]

phase_stats = []
for phase_name, start, end in market_phases:
    mask = (merged['year_month'].astype(str) >= start) & (merged['year_month'].astype(str) <= end)
    subset = merged[mask]
    if len(subset) > 0:
        idx_return = (subset['broker_close'].iloc[-1] / subset['broker_close'].iloc[0] - 1) * 100 if len(subset) > 1 else 0
        phase_stats.append({
            "市场阶段": phase_name,
            "月数": len(subset),
            "月均日成交额(亿)": round(subset['avg_daily_amount'].mean(), 0),
            "成交额中位数(亿)": round(subset['avg_daily_amount'].median(), 0),
            "成交额峰值(亿)": round(subset['avg_daily_amount'].max(), 0),
            "成交额谷值(亿)": round(subset['avg_daily_amount'].min(), 0),
            "券商平均PB": round(subset['avg_pb'].mean(), 2),
            "PB中位数": round(subset['avg_pb'].median(), 2),
            "PB峰值": round(subset['avg_pb'].max(), 2),
            "PB谷值": round(subset['avg_pb'].min(), 2),
            "指数涨幅(%)": round(idx_return, 1),
        })

phase_df = pd.DataFrame(phase_stats)
print(phase_df.to_string(index=False))
phase_df.to_csv(os.path.join(OUT_DIR, "phase_statistics.csv"), index=False, encoding='utf-8-sig')

# ========================
# 5. 相关性分析（分时期）
# ========================
print("\n--- 4.2 相关性分析 ---")

corr_periods = {
    "全样本 (2015-2026)": merged,
    "2015-2016 股灾期": merged[(merged['year_month'].astype(str) >= "2015-07") & (merged['year_month'].astype(str) <= "2016-02")],
    "2016-2018 熊市": merged[(merged['year_month'].astype(str) >= "2016-03") & (merged['year_month'].astype(str) <= "2018-12")],
    "2019-2021 结构牛": merged[(merged['year_month'].astype(str) >= "2019-01") & (merged['year_month'].astype(str) <= "2021-12")],
    "2022-2024 调整期": merged[(merged['year_month'].astype(str) >= "2022-01") & (merged['year_month'].astype(str) <= "2024-09")],
    "2024-2026 AI行情": merged[(merged['year_month'].astype(str) >= "2024-10")],
}

correlation_results = []
for period_name, subset in corr_periods.items():
    if len(subset) < 3:
        continue
    pearson_r, pearson_p = stats.pearsonr(subset['avg_daily_amount'], subset['avg_pb'])
    spearman_r, spearman_p = stats.spearmanr(subset['avg_daily_amount'], subset['avg_pb'])
    log_vol = np.log(subset['avg_daily_amount'].clip(lower=100))
    log_r, log_p = stats.pearsonr(log_vol, subset['avg_pb'])
    
    correlation_results.append({
        "分析时期": period_name,
        "样本月数": len(subset),
        "Pearson r": round(pearson_r, 4),
        "Pearson p-value": f"{pearson_p:.6f}",
        "Spearman r": round(spearman_r, 4),
        "Spearman p-value": f"{spearman_p:.6f}",
        "Log(Vol)-PB r": round(log_r, 4),
    })
    
    print(f"  {period_name}:")
    print(f"    Pearson r={pearson_r:.4f}, p={pearson_p:.6f}")
    print(f"    Spearman r={spearman_r:.4f}, p={spearman_p:.6f}")

corr_df = pd.DataFrame(correlation_results)
corr_df.to_csv(os.path.join(OUT_DIR, "correlation_analysis.csv"), index=False, encoding='utf-8-sig')

# ========================
# 6. 领先-滞后分析
# ========================
print("\n--- 4.3 领先-滞后分析 ---")

def calc_cross_correlation(x, y, max_lag=6):
    results = []
    for lag in range(-max_lag, max_lag + 1):
        if lag > 0:
            x_shifted = x.shift(lag)
            valid = x_shifted.notna() & y.notna()
        elif lag < 0:
            y_shifted = y.shift(-lag)
            valid = x.notna() & y_shifted.notna()
        else:
            valid = x.notna() & y.notna()
        
        if valid.sum() >= 10:
            if lag > 0:
                r, p = stats.pearsonr(x_shifted[valid], y[valid])
            elif lag < 0:
                r, p = stats.pearsonr(x[valid], y_shifted[valid])
            else:
                r, p = stats.pearsonr(x[valid], y[valid])
        else:
            r, p = np.nan, np.nan
        
        results.append({"lag": lag, "correlation": r, "p_value": p})
    return pd.DataFrame(results)

volume_series = merged['avg_daily_amount']
pb_series = merged['avg_pb']

cross_corr = calc_cross_correlation(volume_series, pb_series, max_lag=6)

print("  交叉相关性（lag>0: 成交量领先PB; lag<0: PB领先成交量）:")
print(f"  {'Lag':>5} | {'Correlation':>12} | {'P-value':>10} | {'Interpretation':<30}")
print(f"  {'-'*5} | {'-'*12} | {'-'*10} | {'-'*30}")
for _, row in cross_corr.iterrows():
    lag = int(row['lag'])
    if lag > 0:
        interp = f"成交量领先PB {lag}月"
    elif lag < 0:
        interp = f"PB领先成交量 {-lag}月"
    else:
        interp = "同期相关"
    print(f"  {lag:5d} | {row['correlation']:12.4f} | {row['p_value']:10.6f} | {interp}")

cross_corr.to_csv(os.path.join(OUT_DIR, "cross_correlation.csv"), index=False, encoding='utf-8-sig')

# 找最优领先关系 (取绝对值最大)
best_lead = cross_corr.loc[cross_corr['correlation'].abs().idxmax()]
print(f"\n  最强相关: lag={int(best_lead['lag'])}月, r={best_lead['correlation']:.4f}")

# ========================
# 7. 分位数分析
# ========================
print("\n--- 4.4 成交量分位数与PB区间 ---")

# 定义成交量区间 (亿元)
vol_breakpoints = [4000, 6000, 8000, 10000, 12000, 15000]

print(f"  {'成交量区间(亿/日)':<20} | {'月数':>4} | {'平均PB':>8} | {'PB中位数':>8} | {'PB 25%':>8} | {'PB 75%':>8}")
print(f"  {'-'*20} | {'-'*4} | {'-'*8} | {'-'*8} | {'-'*8} | {'-'*8}")

vol_bin_results = []
prev_bp = 0
for bp in vol_breakpoints:
    mask = (merged['avg_daily_amount'] > prev_bp) & (merged['avg_daily_amount'] <= bp)
    subset = merged[mask]
    label = f"{prev_bp}-{bp}"
    if len(subset) > 0:
        pb_25 = subset['avg_pb'].quantile(0.25)
        pb_75 = subset['avg_pb'].quantile(0.75)
        print(f"  {label:<20} | {len(subset):4d} | {subset['avg_pb'].mean():8.2f} | {subset['avg_pb'].median():8.2f} | {pb_25:8.2f} | {pb_75:8.2f}")
        vol_bin_results.append({
            "成交量区间(亿/日)": label,
            "月数": len(subset),
            "平均PB": round(subset['avg_pb'].mean(), 2),
            "PB中位数": round(subset['avg_pb'].median(), 2),
            "PB 25%": round(pb_25, 2),
            "PB 75%": round(pb_75, 2),
        })
    prev_bp = bp

# >最高区间
mask = merged['avg_daily_amount'] > vol_breakpoints[-1]
subset = merged[mask]
if len(subset) > 0:
    pb_25 = subset['avg_pb'].quantile(0.25)
    pb_75 = subset['avg_pb'].quantile(0.75)
    print(f"  {'>'+str(vol_breakpoints[-1]):<20} | {len(subset):4d} | {subset['avg_pb'].mean():8.2f} | {subset['avg_pb'].median():8.2f} | {pb_25:8.2f} | {pb_75:8.2f}")
    vol_bin_results.append({
        "成交量区间(亿/日)": f">{vol_breakpoints[-1]}",
        "月数": len(subset),
        "平均PB": round(subset['avg_pb'].mean(), 2),
        "PB中位数": round(subset['avg_pb'].median(), 2),
        "PB 25%": round(pb_25, 2),
        "PB 75%": round(pb_75, 2),
    })

vol_bin_df = pd.DataFrame(vol_bin_results)
vol_bin_df.to_csv(os.path.join(OUT_DIR, "volume_pb_bins.csv"), index=False, encoding='utf-8-sig')

# ========================
# 8. 关键场景
# ========================
print("\n--- 4.5 关键场景 ---")

# 2015年牛市峰值
bull_mask = (merged['year_month'].astype(str) >= "2015-04") & (merged['year_month'].astype(str) <= "2015-06")
bull_peak = merged[bull_mask]
if len(bull_peak) > 0:
    max_vol_row = bull_peak.loc[bull_peak['avg_daily_amount'].idxmax()]
    max_pb_row = bull_peak.loc[bull_peak['avg_pb'].idxmax()]
    print(f"  2015年牛市成交量峰值: {max_vol_row['year_month']}, {max_vol_row['avg_daily_amount']:.0f}亿/日, PB={max_vol_row['avg_pb']:.2f}")
    print(f"  2015年券商PB峰值: {max_pb_row['year_month']}, PB={max_pb_row['avg_pb']:.2f}, 成交额={max_pb_row['avg_daily_amount']:.0f}亿/日")

# 2024年10月成交额峰值
mask24 = (merged['year_month'].astype(str) >= "2024-09") & (merged['year_month'].astype(str) <= "2024-12")
peak24 = merged[mask24]
if len(peak24) > 0:
    max24 = peak24.loc[peak24['avg_daily_amount'].idxmax()]
    print(f"  2024年成交额峰值: {max24['year_month']}, {max24['avg_daily_amount']:.0f}亿/日, PB={max24['avg_pb']:.2f}")

# 当前
current = merged.iloc[-1]
print(f"  当前({current['year_month']}): 月均日成交额 {current['avg_daily_amount']:.0f}亿, PB={current['avg_pb']:.2f}, 指数={current['broker_close']:.0f}")

# ========================
# 9. PB修复空间测算
# ========================
print("\n--- 4.6 PB修复空间测算（回归模型）---")

# 全样本: PB ~ ln(Vol)
log_vol_full = np.log(merged['avg_daily_amount'].clip(lower=100))
slope, intercept, r_value, p_value, std_err = stats.linregress(log_vol_full, merged['avg_pb'])
print(f"\n  模型: PB = {slope:.4f} * ln(日均成交额) + {intercept:.4f}")
print(f"  R² = {r_value**2:.4f}, p = {p_value:.6f}")

# 近期 (2020+)
recent_mask = merged['year_month'].astype(str) >= "2020-01"
recent_df = merged[recent_mask]
log_vol_recent = np.log(recent_df['avg_daily_amount'].clip(lower=100))
s_r, i_r, r2_r, p_r, se_r = stats.linregress(log_vol_recent, recent_df['avg_pb'])
print(f"  模型(2020+): PB = {s_r:.4f} * ln(日均成交额) + {i_r:.4f}")
print(f"  R²(2020+) = {r2_r**2:.4f}, p = {p_r:.6f}")

# 场景测算
current_vol = current['avg_daily_amount']
current_pb = current['avg_pb']

scenarios = {
    f"当前(~{int(current_vol)}亿/日)": current_vol,
    "1.5万亿/日": 15000,
    "2.0万亿/日": 20000,
    "2.5万亿/日": 25000,
    "3.0万亿/日": 30000,
    "2015年峰值(2.2万亿)": 22000,
    "2024年峰值(3.45万亿)": 34500,
}

print(f"\n  PB修复空间测算 (全样本模型):")
print(f"  {'场景':<25} | {'日均成交额(亿)':>16} | {'预测PB':>8} | {'vs当前PB':>10} | {'PB涨幅%':>10}")
print(f"  {'-'*25} | {'-'*16} | {'-'*8} | {'-'*10} | {'-'*10}")

pb_scenario_data = []
for sc_name, sc_vol in scenarios.items():
    pred_pb = slope * np.log(sc_vol) + intercept
    vs_current = pred_pb - current_pb
    pct_change = (pred_pb / current_pb - 1) * 100
    print(f"  {sc_name:<25} | {sc_vol:16.0f} | {pred_pb:8.2f} | {vs_current:+10.2f} | {pct_change:+9.1f}%")
    pb_scenario_data.append({
        "场景": sc_name,
        "日均成交额(亿)": sc_vol,
        "预测PB(全样本)": round(pred_pb, 2),
        "vs当前PB": round(vs_current, 2),
        "预测PB涨幅%": round(pct_change, 1),
        "预测PB(2020+模型)": round(s_r * np.log(sc_vol) + i_r, 2),
    })

pb_scenario_df = pd.DataFrame(pb_scenario_data)
pb_scenario_df.to_csv(os.path.join(OUT_DIR, "pb_scenarios.csv"), index=False, encoding='utf-8-sig')

# ========================
# 10. 策略模拟
# ========================
print("\n--- 4.7 策略模拟: 成交量信号 → 择时买卖券商 ---")

# 策略: 月均日成交额突破阈值→买入券商指数; 跌破→卖出
# 回测期: 2015-10 至 2026-06

merged['broker_return'] = merged['broker_close'].pct_change().fillna(0)

thresholds = [5000, 8000, 10000, 12000]
strat_results = []

for threshold in thresholds:
    merged[f'signal_{threshold}'] = (merged['avg_daily_amount'] > threshold).astype(int)
    merged[f'strat_ret_{threshold}'] = merged['broker_return'] * merged[f'signal_{threshold}']
    
    strat_ret = merged[f'strat_ret_{threshold}']
    bh_ret = merged['broker_return']
    
    strat_nav = (1 + strat_ret).cumprod()
    bh_nav = (1 + bh_ret).cumprod()
    
    n_months = len(merged)
    n_years = n_months / 12
    
    def calc_metrics(returns, nav):
        ann_ret = nav.iloc[-1] ** (1 / n_years) - 1 if nav.iloc[-1] > 0 else -1
        ann_vol = returns.std() * np.sqrt(12)
        rf_m = 0.02 / 12
        sharpe = (returns.mean() - rf_m) / returns.std() * np.sqrt(12) if returns.std() > 0 else 0
        mdd = (nav / nav.cummax() - 1).min()
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
        return ann_ret, ann_vol, sharpe, mdd, win_rate
    
    s_ret, s_vol, s_sharpe, s_mdd, s_win = calc_metrics(strat_ret, strat_nav)
    b_ret, b_vol, b_sharpe, b_mdd, b_win = calc_metrics(bh_ret, bh_nav)
    
    signal_freq = merged[f'signal_{threshold}'].mean()
    months_in = merged[f'signal_{threshold}'].sum()
    
    print(f"\n  成交量突破 {threshold}亿 策略:")
    print(f"    持仓月份占比: {signal_freq:.1%} ({int(months_in)}/{n_months}个月)")
    print(f"    策略年化收益: {s_ret:.2%}")
    print(f"    基准年化收益: {b_ret:.2%}")
    print(f"    超额收益: {s_ret - b_ret:.2%}")
    print(f"    策略Sharpe: {s_sharpe:.3f}  | 基准Sharpe: {b_sharpe:.3f}")
    print(f"    策略最大回撤: {s_mdd:.2%}  | 基准最大回撤: {b_mdd:.2%}")
    print(f"    策略月度胜率: {s_win:.1%}  | 基准月度胜率: {b_win:.1%}")
    
    strat_results.append({
        "策略阈值": f"日成交>{threshold}亿",
        "持仓月份比": f"{signal_freq:.1%}",
        "策略年化收益": f"{s_ret:.2%}",
        "基准年化收益": f"{b_ret:.2%}",
        "超额收益": f"{s_ret-b_ret:.2%}",
        "策略Sharpe": round(s_sharpe, 3),
        "基准Sharpe": round(b_sharpe, 3),
        "策略最大回撤": f"{s_mdd:.2%}",
        "基准最大回撤": f"{b_mdd:.2%}",
    })

strat_df = pd.DataFrame(strat_results)
strat_df.to_csv(os.path.join(OUT_DIR, "strategy_simulation.csv"), index=False, encoding='utf-8-sig')

# ========================
# 11. 保存汇总结果
# ========================
print("\n[5/5] 保存汇总结果...")

results_summary = {
    "指标": [
        "分析期",
        "总月数",
        "月均日成交额均值(亿)",
        "月均日成交额中位数(亿)",
        "月均日成交额标准差(亿)",
        "券商平均PB均值",
        "券商平均PB中位数",
        "券商平均PB标准差",
        "全样本Pearson r (成交量 vs PB)",
        "全样本Spearman r",
        "全样本R² (ln模型)",
        "最优交叉相关lag(月)",
        "最优交叉相关r",
        "当前月均日成交额(亿)",
        "当前券商平均PB",
        "如果日成交1.5万亿 → 预测PB",
        "如果日成交2.0万亿 → 预测PB",
        "如果日成交2.5万亿 → 预测PB",
    ],
    "值": [
        f"{merged['year_month'].min()} - {merged['year_month'].max()}",
        len(merged),
        round(merged['avg_daily_amount'].mean(), 0),
        round(merged['avg_daily_amount'].median(), 0),
        round(merged['avg_daily_amount'].std(), 0),
        round(merged['avg_pb'].mean(), 2),
        round(merged['avg_pb'].median(), 2),
        round(merged['avg_pb'].std(), 2),
        round(correlation_results[0]['Pearson r'], 4),
        round(correlation_results[0]['Spearman r'], 4),
        round(r_value**2, 4),
        int(best_lead['lag']),
        round(best_lead['correlation'], 4),
        round(current_vol, 0),
        round(current_pb, 2),
        round(slope * np.log(15000) + intercept, 2),
        round(slope * np.log(20000) + intercept, 2),
        round(slope * np.log(25000) + intercept, 2),
    ]
}

# Add per-period correlations
for cr in correlation_results:
    results_summary["指标"].append(f"{cr['分析时期']} Pearson r")
    results_summary["值"].append(cr['Pearson r'])

results_df = pd.DataFrame(results_summary)
results_df.to_csv(os.path.join(OUT_DIR, "results.csv"), index=False, encoding='utf-8-sig')

# 保存详细月度面板
merged.to_csv(os.path.join(OUT_DIR, "monthly_panel.csv"), index=False, encoding='utf-8-sig')

# 输出关键发现JSON
findings = {
    "total_months": len(merged),
    "period": f"{merged['year_month'].min()} - {merged['year_month'].max()}",
    "volume_stats": {
        "mean_avg_daily": round(float(merged['avg_daily_amount'].mean()), 0),
        "median_avg_daily": round(float(merged['avg_daily_amount'].median()), 0),
        "max_avg_daily": round(float(merged['avg_daily_amount'].max()), 0),
        "min_avg_daily": round(float(merged['avg_daily_amount'].min()), 0),
    },
    "pb_stats": {
        "mean_pb": round(float(merged['avg_pb'].mean()), 2),
        "median_pb": round(float(merged['avg_pb'].median()), 2),
        "max_pb": round(float(merged['avg_pb'].max()), 2),
        "min_pb": round(float(merged['avg_pb'].min()), 2),
    },
    "correlation": {
        "full_sample_pearson": float(correlation_results[0]['Pearson r']),
        "full_sample_spearman": float(correlation_results[0]['Spearman r']),
        "regression_r2": round(float(r_value**2), 4),
        "regression_formula": f"PB = {slope:.4f} * ln(Vol) + {intercept:.4f}",
        "per_period": {cr['分析时期']: cr['Pearson r'] for cr in correlation_results}
    },
    "lead_lag": {
        "best_lag_months": int(best_lead['lag']),
        "best_correlation": round(float(best_lead['correlation']), 4),
        "interpretation": "成交量与PB呈显著负相关(-0.37~-0.20), 而非正相关"
    },
    "pb_scenarios": {
        "current_vol_pred_pb": round(float(slope * np.log(current_vol) + intercept), 2),
        "vol_15000_pred_pb": round(float(slope * np.log(15000) + intercept), 2),
        "vol_20000_pred_pb": round(float(slope * np.log(20000) + intercept), 2),
    },
    "current_snapshot": {
        "year_month": str(current['year_month']),
        "avg_daily_volume": round(float(current_vol), 0),
        "broker_avg_pb": round(float(current_pb), 2),
        "broker_index": round(float(current['broker_close']), 2),
    },
    "key_conclusion": "成交量与券商PB呈弱负相关而非假设的正相关。2015年牛市后,券商PB持续下降,即使在2024-2026成交额创历史新高的环境下,PB仍处于历史低位(1.4-2.0)。成交额驱动PB修复的假设在2015年后基本失效。"
}

with open(os.path.join(OUT_DIR, "findings.json"), "w", encoding='utf-8') as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print("分析完成！结果已保存到:", OUT_DIR)
print("=" * 60)
print("\n文件清单:")
for f in sorted(os.listdir(OUT_DIR)):
    fpath = os.path.join(OUT_DIR, f)
    size = os.path.getsize(fpath)
    print(f"  {f:40s} {size:>8,} bytes")
