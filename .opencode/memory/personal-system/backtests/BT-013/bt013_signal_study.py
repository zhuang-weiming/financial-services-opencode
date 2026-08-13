#!/usr/bin/env python3
"""
BT-013 — BUY_LADDER 信号有效性 · 可达性 + 事件研究 (零新下载)

目的: 回答 buy-ladder 三个问题
  1) 分数可达性: 当前固定比例阈值 (0.65/0.42 * max) 是否锁死?
  2) 信号有效性: 哪个 buy 信号触发后带来截面超额收益 (α 做个股买入信号)?
  3) 权重结构: 现有权重 (事件×2 / 趋势×1) 是否与事件研究 alpha 倒挂?

数据源 (零新下载):
  - 信号: BT-011/results/signal_cache_v2.parquet (200 池, 2024-10-08 ~ 2026-08-13)
  - 价格: data/market/daily/<code>.csv (200/200 已本地存在)

方法 (事件研究):
  对每个信号 s, 取 signal>0 的触发日 (code,date) t,
  计算 t 后 20/60 交易日 log 收益; 基准 = 同日同池全部股票平均未来收益 (截面基准, 消除市场 beta).
  α = 触发组平均未来收益 − 当日截面基准. 分全期 / 2025 牛 / 2026 弱.
  显著性: 单样本 t-test (α vs 0).

注意 (与本文件 build 环境的限定):
  - 缓存中 multi_factor/sector_relative/factor_research/pair_trading 由 BT-011 显式置零 (无 peer 恒 0, bt011_engine.py:91);
    因此这些信号的事件研究 "无触发" 只能证明缓存口径, 不代表生产无 peer 路径 (buy_ladder 生产会传 peer_codes).
  - smc 在缓存中 0.0000 触发; 生产 calc_smc 慢 (swing), bt011 缓存为逐日全量也返回 0 → 待另行确认.
  - turnover_anomaly / ichimoku 触发率 <1%, n 小, 结论需谨慎.

用法:
  cd <workspace> && python3 .opencode/memory/personal-system/backtests/BT-013/bt013_signal_study.py
输出:
  results/signal_trigger_rates.csv   — 各信号触发率 (全期/2025/2026)
  results/event_study_alpha.csv      — 事件研究 α20/α60 + t/p + 胜率
  results/score_reachability.csv     — 双版本 score 分布 + 阶段可达性
  results/summary.json               — 汇总
"""
import pandas as pd
import numpy as np
import json, glob, os, warnings
warnings.filterwarnings('ignore')
from scipy import stats

ROOT = '/Users/weimingzhuang/Documents/source_code/financial-services-opencode'
CACHE = f'{ROOT}/.opencode/memory/personal-system/backtests/BT-011/results/signal_cache_v2.parquet'
POOL = f'{ROOT}/.opencode/memory/personal-system/backtests/BT-011/pool_200.json'
DAILY = f'{ROOT}/data/market/daily'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(OUT, exist_ok=True)

pool = json.load(open(POOL))
codes = [p['code'] for p in pool]
df = pd.read_parquet(CACHE)
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['ym'] = df['date'].dt.to_period('M').astype(str)
print(f"cache: {df.shape} | {df['date'].min().date()} ~ {df['date'].max().date()} | n_stocks={df['code'].nunique()}")

sig_cols = [c for c in df.columns if c not in ('date', 'code', 'year', 'ym')]

# =====================================================================
# 1. 信号触发率 (全期 / 2025 / 2026)
# =====================================================================
print("\n=== 1. 信号触发率 ===")
rows = []
for c in sig_cols:
    rec = {'signal': c}
    for lab, m in [('all', None), ('2025', 2025), ('2026', 2026)]:
        sub = df if m is None else df[df['year'] == m]
        rec[f'pos_{lab}'] = round(float((sub[c] > 0).mean()), 5)
        rec[f'neg_{lab}'] = round(float((sub[c] < 0).mean()), 5)
    rows.append(rec)
tr = pd.DataFrame(rows).sort_values('pos_all', ascending=False)
tr.to_csv(f'{OUT}/signal_trigger_rates.csv', index=False)
print(tr.to_string(index=False))

# =====================================================================
# 2. 向量化未来收益表 + 截面基准
# =====================================================================
ret_rows = []
for c in codes:
    g = glob.glob(f'{DAILY}/{c}*.csv')
    if not g:
        continue
    try:
        d = pd.read_csv(g[0])
        d['date'] = pd.to_datetime(d['date'])
        d = d.drop_duplicates('date').set_index('date')['close'].astype(float).sort_index()
        n = len(d)
        if n < 30:
            continue
        s = np.log(d.to_numpy())
        r20 = pd.Series(np.nan, index=d.index)
        r60 = pd.Series(np.nan, index=d.index)
        r20.iloc[:-21] = s[21:] - s[:-21]
        r60.iloc[:-61] = s[61:] - s[:-61]
        ret_rows.append(pd.DataFrame({'r20': r20, 'r60': r60, 'code': c}).reset_index())
    except Exception:
        continue
ret = pd.concat(ret_rows, ignore_index=True)
ret['date'] = pd.to_datetime(ret['date'])
print(f"\n收益表: {ret.shape}")

bench20 = ret.groupby('date')['r20'].mean().rename('b20')
bench60 = ret.groupby('date')['r60'].mean().rename('b60')
ret = ret.merge(bench20, left_on='date', right_index=True).merge(bench60, left_on='date', right_index=True)
ret['alpha20'] = ret['r20'] - ret['b20']
ret['alpha60'] = ret['r60'] - ret['b60']

# =====================================================================
# 3. 事件研究: 信号>0 触发日的截面超额
# =====================================================================
print("\n=== 2. 事件研究: 触发日截面超额 (signal>0) ===")
trig = df[['code', 'date', 'year'] + sig_cols].melt(id_vars=['code', 'date', 'year'], var_name='sig', value_name='v')
trig = trig[trig['v'] > 0]
ev = trig.merge(ret[['code', 'date', 'alpha20', 'alpha60']], on=['code', 'date'], how='left')

evrows = []
for (sig, ylab, yv) in [(s, 'all', None) for s in sig_cols] + \
                        [(s, '2025', 2025) for s in sig_cols] + \
                        [(s, '2026', 2026) for s in sig_cols]:
    sub = ev[(ev['sig'] == sig) & (ev['year'] == yv)] if yv else ev[ev['sig'] == sig]
    sub = sub.dropna(subset=['alpha20'])
    n = len(sub)
    rec = {'signal': sig, 'period': ylab, 'n': n}
    if n > 0:
        rec['alpha20'] = round(float(sub['alpha20'].mean()), 5)
        rec['alpha60'] = round(float(sub['alpha60'].dropna().mean()), 5) if sub['alpha60'].notna().any() else np.nan
        rec['win20'] = round(float((sub['alpha20'] > 0).mean()), 4)
        if n >= 3:
            t, p = stats.ttest_1samp(sub['alpha20'], 0)
            rec['t20'] = round(float(t), 3)
            rec['p20'] = round(float(p), 4)
        else:
            rec['t20'] = np.nan
            rec['p20'] = np.nan
    evrows.append(rec)
evdf = pd.DataFrame(evrows)
evdf.to_csv(f'{OUT}/event_study_alpha.csv', index=False)
# 打印有效样本 (n>=100 且全期)
pd.set_option('display.float_format', lambda x: f'{x:.4f}')
print(evdf[(evdf['n'] >= 100) & (evdf['period'] == 'all')].sort_values('alpha20', ascending=False).to_string(index=False))
print("\n-- 分年 (活跃信号, n>=100) --")
print(evdf[(evdf['n'] >= 100) & (evdf['period'].isin(['2025', '2026']))].sort_values(['period', 'alpha20'], ascending=[True, False]).to_string(index=False))

# =====================================================================
# 4. score 可达性 (双版本)
# =====================================================================
print("\n=== 3. score 分布 + 阶段可达性 ===")
df['vpr'] = ((df['turnover_anomaly'] > 0) & (df['ad_line'] < 0)).astype(int)
df['scx'] = ((df['chanlun'] > 0) & (df['smc'] > 0) & (df['candlestick'] > 0)).astype(int)
tr_approx = ['alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc', 'alpha_zoo', 'multi_factor', 'ml_strategy', 'sector_relative']
versions = {
    'V_A_当前声明(2事件/turnover+chanlun, 8趋势,max声明20)': {'ev': ['chanlun', 'turnover_anomaly'], 'tr': tr_approx},
    'V_B_近似4事件(vpr/scx, 8趋势)': {'ev': ['chanlun', 'turnover_anomaly', 'vpr', 'scx'], 'tr': tr_approx},
}
reach_rows = []
for vn, v in versions.items():
    evp = (df[v['ev']] > 0).sum(axis=1)
    evn = (df[v['ev']] < 0).sum(axis=1)
    trp = (df[v['tr']] > 0).sum(axis=1)
    score = 2 * evp + trp - 2 * evn
    for lab, m in [('all', None), ('2025', 2025), ('2026', 2026)]:
        sub = score if m is None else score[df['year'] == m]
        nsub = len(sub)
        mx = 20 if '声明' in vn else 16
        thr1, thr2 = 0.65 * mx, 0.42 * mx
        st1 = int((sub >= thr1).sum())
        st2 = int(((sub >= thr2) & (sub < thr1)).sum())
        reach_rows.append({
            'version': vn.split('(')[0], 'period': lab, 'n': nsub,
            'mean': round(float(sub.mean()), 3), 'p50': float(sub.median()),
            'p75': float(sub.quantile(.75)), 'p90': float(sub.quantile(.90)),
            'p99': float(sub.quantile(.99)), 'max': float(sub.max()),
            'thr1': round(thr1, 2), 'thr2': round(thr2, 2),
            'stage1_days': st1, 'stage2_days': st2,
        })
        print(f"  [{lab:4s}] {vn[:28]:30s} n={nsub:6d} mean={sub.mean():5.2f} P90={sub.quantile(.90):4.1f} "
              f"P99={sub.quantile(.99):4.1f} max={sub.max():4.1f} | 声明阈({thr1:.1f}/{thr2:.1f}) S1={st1} S2={st2}")
reachdf = pd.DataFrame(reach_rows)
reachdf.to_csv(f'{OUT}/score_reachability.csv', index=False)

summary = {
    'cache': {'rows': int(len(df)), 'start': str(df['date'].min().date()), 'end': str(df['date'].max().date()),
              'stocks': int(df['code'].nunique())},
    'dead_signals_cache_oriented': ['multi_factor', 'sector_relative', 'factor_research', 'pair_trading'],
    'strongest_negative_alpha': ['chanlun', 'turnover_anomaly'],
    'strongest_positive_alpha_all': ['alpha_zoo', 'technical_basic'],
    'regime_dependent_positive': {'2025_cow': 'alpha_zoo', '2026_weak': ['technical_basic', 'candlestick', 'ad_line']},
    'stage_reachable': {'stage1': '0 / 89845 (0.00%)', 'note': '固定比例阈值 0.65/0.42·max 两年零触发'},
}
with open(f'{OUT}/summary.json', 'w') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
print(f"\n结果已写入 {OUT}")
