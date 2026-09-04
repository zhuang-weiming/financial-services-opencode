#!/usr/bin/env python3
"""
BT-017 — "信心系数缩放仓位 vs 均匀50%仓位" validation (BUY_LADDER v4.0 sizing hypothesis)

Research-only. NO trading.

Question: replace BUY_LADDER v3.1's fixed 50% first tranche with a
multiplicative confidence-factor sizing model:
    final_position% = base_weight(score) * prod(confidence_factor_i)
    floor = 0.5% (venture), cap = 2*base_weight; only the 5 hard vetoes can zero a signal

Data (zero new downloads except fundamentals, cached):
  - signals: BT-011/results/signal_cache_v2.parquet (16 signals, 200 pool, 2024-10-08..2026-08-13)
  - prices:  data/market/daily/<code>*.csv (900 bars; close/vol/ohlc)
  - regime:  data/market/daily/510300.csv (CSI300 ETF, MA60 proxy — same as buy_ladder Layer-0)
  - fundamentals: results/fundamentals_raw.json (akshare stock_financial_abstract ROE/debt FY2023-25
    + stock_zh_valuation_baidu PB 3y) — fetched once, PIT-mapped by annual-report deadlines

Scoring (BT-016 W_B): score = 2*I(technical_basic>0) + 2*I(alpha_zoo>0)
                            + 1*I(candlestick>0) + 1*I(ad_line>0), max 6
  >=4 -> 击球区 (v3.1 50% first tranche), >=3 -> 观察区

Event definition: first event per code per 60-trading-day window where score>=3.
Forward returns 20/60d close-to-close; excess vs same-day same-pool equal-weight
benchmark (BT-013/014/015/016 convention).

Variants (all evaluated on the SAME clustered >=3 event set; >=4 subset for v3.1 parity):
  V0 skip (0%)             — context (does nothing)
  V1 uniform 50% (>=4)     — v3.1 status quo
  V2 uniform 100% (>=4)    — context
  V3 conf-scaled (>=3)     — full 8-factor model, base=0.30@score3 / 0.50@score4+
  V4 conf-scaled (>=4)     — full 8-factor model on 击球区 only (parity vs V1/V2)
Sensitivity: cap/floor grid, per-year split, factor OAT.

Portfolio sim (per-event equal-weight, mark-to-market, no leverage):
  - each event opens a position sized pos_i * NAV at entry close, held `hold`
    trading days; concurrent positions' weights are pro-rata scaled so total
    exposure <= 100% of NAV (fully-invested, no leverage); idle cash earns 0.
  - daily NAV mark-to-market; report ann. Sharpe, max DD, total return.
"""
import pandas as pd
import numpy as np
import json, os, glob, warnings
from scipy import stats
warnings.filterwarnings('ignore')

ROOT = '/Users/weimingzhuang/Documents/source_code/financial-services-opencode'
CACHE = f'{ROOT}/.opencode/memory/personal-system/backtests/BT-011/results/signal_cache_v2.parquet'
POOL = f'{ROOT}/.opencode/memory/personal-system/backtests/BT-011/pool_200.json'
DAILY = f'{ROOT}/data/market/daily'
FUND_RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'fundamentals_raw.json')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(OUT, exist_ok=True)

pool = json.load(open(POOL))
codes = [p['code'] for p in pool]
fund_raw = json.load(open(FUND_RAW))

# =====================================================================
# 0. Load cache, compute score
# =====================================================================
df = pd.read_parquet(CACHE)
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
W = {'technical_basic': 2, 'alpha_zoo': 2, 'candlestick': 1, 'ad_line': 1}
score = sum(df[k].gt(0).astype(int) * w for k, w in W.items())
df['score'] = score
print(f"cache {df.shape} | score>=3: {(df['score']>=3).sum()} | >=4: {(df['score']>=4).sum()}")

# =====================================================================
# 1. Load daily prices
# =====================================================================
price_dfs = {}
for c in codes:
    g = glob.glob(f'{DAILY}/{c}*.csv')
    if not g:
        continue
    try:
        d = pd.read_csv(g[0])
        d['date'] = pd.to_datetime(d['date'])
        d = d.drop_duplicates('date').set_index('date')
        d = d[['open', 'close', 'high', 'low', 'volume']].astype(float)
        price_dfs[c] = d.sort_index()
    except Exception:
        continue
print(f"price coverage: {len(price_dfs)}/{len(codes)}")

# =====================================================================
# 2. Technical features per code
# =====================================================================
def build_features(code: str, d: pd.DataFrame):
    close = d['close']
    volume = d['volume']
    lr = np.log(close / close.shift(1))
    vol60 = lr.rolling(60).std() * np.sqrt(252)
    turnover_yi = (volume * close) / 1e8
    high, low = d['high'], d['low']
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    up = high.diff()
    dn = -low.diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=d.index)
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=d.index)
    atr = tr.ewm(alpha=1 / 14, min_periods=14).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / 14, min_periods=14).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / 14, min_periods=14).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / 14, min_periods=14).mean()
    hlc3 = (high + low + close) / 3
    esa = hlc3.ewm(span=10, adjust=False).mean()
    de = (hlc3 - esa).abs().ewm(span=10, adjust=False).mean()
    ci = (hlc3 - esa) / (0.015 * de)
    wt1 = ci.ewm(span=21, adjust=False).mean()
    return pd.DataFrame({'vol60_ann': vol60, 'turnover_yi': turnover_yi,
                         'adx': adx, 'wt1': wt1}, index=d.index)

feat_cache = {c: build_features(c, d) for c, d in price_dfs.items()}

# =====================================================================
# 3. Fundamentals (PIT)
# =====================================================================
def fy_for_date(date):
    if date <= pd.Timestamp('2025-04-30'):
        return '20231231'
    if date <= pd.Timestamp('2026-04-30'):
        return '20241231'
    return '20251231'

def pb_pctile(code: str, date: pd.Timestamp):
    rec = fund_raw.get(code, {})
    pb = rec.get('pb')
    if not pb:
        return None
    s = pd.Series(pb['pb'], index=pd.to_datetime(pb['date'])).sort_index()
    s = s[s.index <= date]
    if len(s) < 60:
        return None
    win = s.iloc[-252:]
    cur = s.iloc[-1]
    return float((win <= cur).mean())

def fund_factors(code: str, date: pd.Timestamp):
    rec = fund_raw.get(code, {})
    fyd = rec.get('roe_debt_by_fy') or {}
    fy = fy_for_date(date)
    y = fyd.get(fy) or {}
    roe, debt = y.get('roe'), y.get('debt')
    f_fund = None
    if roe is not None:
        f_fund = 1.2 if roe > 10 else (1.0 if roe >= 0 else 0.6)
        if debt is not None and debt > 90:
            f_fund *= 0.7
    pbp = pb_pctile(code, date)
    f_val = None
    if pbp is not None:
        if pbp < 0.20:
            f_val = 1.2
        elif pbp <= 0.50:
            f_val = 1.0
        elif pbp <= 0.70:
            f_val = 0.9
        else:
            f_val = 0.8
    return f_fund, f_val

# =====================================================================
# 4. Regime proxy (CSI300 ETF MA60 — same as buy_ladder Layer-0)
# =====================================================================
regime = None
for g in glob.glob(f'{DAILY}/510300*.csv'):
    if '.bak' in g:
        continue
    r = pd.read_csv(g)
    r['date'] = pd.to_datetime(r['date'])
    r = r.set_index('date')['close'].sort_index()
    ma60 = r.rolling(60).mean()
    regime = pd.DataFrame({'close': r, 'ma60': ma60})
    break

def regime_factor(date: pd.Timestamp):
    if regime is None or date not in regime.index:
        return 1.0
    row = regime.loc[date]
    if pd.isna(row['ma60']):
        return 1.0
    return 1.2 if row['close'] > row['ma60'] else 0.8

# =====================================================================
# 5. Event set — cluster per code: first event per 60-trading-day window
# =====================================================================
def cluster_events(sub: pd.DataFrame, min_gap=60):
    dates = sub.reset_index(drop=True)
    keep, last_pos = [], -10**9
    for i in range(len(dates)):
        if i - last_pos >= min_gap:
            keep.append(i)
            last_pos = i
    return dates.loc[keep]

event_rows = []
for c in codes:
    sub = df[df['code'] == c].sort_values('date')
    if len(sub) == 0:
        continue
    # cluster per tier: >=3 (V3 universe) and >=4 (V0/V1/V2/V4 universe)
    clustered3 = cluster_events(sub[sub['score'] >= 3], 60)
    for _, row in clustered3.iterrows():
        event_rows.append({'code': c, 'date': row['date'], 'score': int(row['score']),
                           'year': int(row['year']), 'tier': 'ge3'})
    clustered4 = cluster_events(sub[sub['score'] >= 4], 60)
    for _, row in clustered4.iterrows():
        event_rows.append({'code': c, 'date': row['date'], 'score': int(row['score']),
                           'year': int(row['year']), 'tier': 'ge4'})

E0 = pd.DataFrame(event_rows)
E0 = E0.drop_duplicates(['code', 'date', 'tier']).sort_values('date').reset_index(drop=True)
print(f"clustered events: ge3={len(E0[E0['tier']=='ge3'])} | ge4={len(E0[E0['tier']=='ge4'])}")

# =====================================================================
# 6. Forward returns + same-pool benchmark
# =====================================================================
ret_rows = []
for c in codes:
    if c not in price_dfs:
        continue
    close = price_dfs[c]['close']
    if len(close) < 90:
        continue
    s = np.log(close.to_numpy())
    idx = close.index
    r20 = pd.Series(np.nan, index=idx)
    r60 = pd.Series(np.nan, index=idx)
    r20.iloc[:-21] = s[21:] - s[:-21]
    r60.iloc[:-61] = s[61:] - s[:-61]
    ret_rows.append(pd.DataFrame({'r20': r20, 'r60': r60, 'code': c}).reset_index())
ret = pd.concat(ret_rows, ignore_index=True)
ret['date'] = pd.to_datetime(ret['date'])
bench20 = ret.groupby('date')['r20'].mean().rename('b20')
bench60 = ret.groupby('date')['r60'].mean().rename('b60')
ret = ret.merge(bench20, left_on='date', right_index=True).merge(bench60, left_on='date', right_index=True)
ret['alpha20'] = ret['r20'] - ret['b20']
ret['alpha60'] = ret['r60'] - ret['b60']

# =====================================================================
# 7. Attach features + factors
# =====================================================================
rows = []
for _, e in E0.iterrows():
    code, date, sc = e['code'], e['date'], int(e['score'])
    d = price_dfs.get(code)
    if d is None or date not in d.index:
        continue
    row = {'code': code, 'date': date, 'score': sc, 'year': int(e['year']), 'tier': e['tier']}
    feats = feat_cache.get(code)
    if feats is not None and date in feats.index:
        f = feats.loc[date]
        row['vol60_ann'] = None if pd.isna(f['vol60_ann']) else float(f['vol60_ann'])
        row['turnover_yi'] = None if pd.isna(f['turnover_yi']) else float(f['turnover_yi'])
        row['adx'] = None if pd.isna(f['adx']) else float(f['adx'])
        row['wt1'] = None if pd.isna(f['wt1']) else float(f['wt1'])
    ff, fv = fund_factors(code, date)
    row['f_fund'] = ff
    row['f_val'] = fv
    row['f_regime'] = regime_factor(date)
    rr = ret[(ret['code'] == code) & (ret['date'] == date)]
    if len(rr):
        row['r20'] = float(rr['r20'].iloc[0])
        row['r60'] = float(rr['r60'].iloc[0])
        row['alpha20'] = float(rr['alpha20'].iloc[0])
        row['alpha60'] = float(rr['alpha60'].iloc[0])
    else:
        row['r20'] = row['r60'] = row['alpha20'] = row['alpha60'] = np.nan
    rows.append(row)

E = pd.DataFrame(rows)
E['date'] = pd.to_datetime(E['date'])
print(f"events with full data: {len(E)} | >=4: {(E['score']>=4).sum()}")

# =====================================================================
# 7b. First-vs-repeat decomposition (why clustered alpha differs from BT-016)
# =====================================================================
raw_all = df[['code', 'date', 'score']].sort_values(['code', 'date']).reset_index(drop=True)
raw_ev = raw_all[raw_all['score'] >= 4].copy()
raw_ev = raw_ev.merge(ret[['code', 'date', 'alpha20', 'alpha60']], on=['code', 'date'], how='left')
first_flags = []
for code, g in raw_ev.groupby('code'):
    mask = np.zeros(len(g), dtype=bool)
    last = -1000
    for i in range(len(g)):
        if i - last >= 60:
            mask[i] = True
            last = i
    first_flags.extend(mask.tolist())
raw_ev['is_first'] = first_flags
decomp_rows = []
for lab, m in [('first_in_60d', raw_ev['is_first'] == True), ('repeat', raw_ev['is_first'] == False)]:
    sub = raw_ev[m]
    rec = {'event_type': lab, 'n': int(len(sub))}
    for h in ['20', '60']:
        a = sub[f'alpha{h}'].dropna()
        rec[f'alpha{h}_mean'] = round(float(a.mean()), 5)
        rec[f'alpha{h}_median'] = round(float(a.median()), 5)
        rec[f'win{h}'] = round(float((a > 0).mean()), 3)
        if len(a) >= 3 and a.std() > 0:
            t, p = stats.ttest_1samp(a, 0)
            rec[f't{h}'] = round(float(t), 2)
            rec[f'p{h}'] = round(float(p), 4)
    decomp_rows.append(rec)
decomp = pd.DataFrame(decomp_rows)
decomp.to_csv(f'{OUT}/bt017_first_vs_repeat.csv', index=False)
print("\n=== First-entry vs repeat events (raw >=4, why clustering matters) ===")
print(decomp.to_string(index=False))
print("NOTE: BT-016 published α60 +1.26% on raw >=4 — that mean is dominated by repeat events.")

# =====================================================================
# 8. Factors
# =====================================================================
def f_signal(sc):
    return {3: 0.85, 4: 1.00, 5: 1.15, 6: 1.30}.get(sc, 1.0)

def f_vol(v):
    if v is None or pd.isna(v):
        return 1.0
    return 1.1 if v < 0.30 else (1.0 if v <= 0.60 else 0.7)

def f_liq(t):
    if t is None or pd.isna(t):
        return 1.0
    return 1.1 if t > 5 else (1.0 if t >= 1 else 0.8)

def f_trend(adx, wt1):
    if adx is None or pd.isna(adx):
        return 1.0
    if adx > 30 and wt1 is not None and not pd.isna(wt1) and wt1 > 0:
        return 1.2
    if 20 <= adx <= 30:
        return 1.0
    if adx < 20:
        return 0.8
    return 1.0

E['f1_sig'] = E['score'].map(f_signal)
E['f2_fund'] = E['f_fund'].fillna(1.0)
E['f3_val'] = E['f_val'].fillna(1.0)
E['f4_vol'] = E['vol60_ann'].map(f_vol)
E['f5_liq'] = E['turnover_yi'].map(f_liq)
E['f6_trend'] = [f_trend(a, w) for a, w in zip(E['adx'], E['wt1'])]
E['f7_regime'] = E['f_regime']
E['f8_analyst'] = 1.0

def base_weight(sc):
    return 0.30 if sc == 3 else 0.50

E['base'] = E['score'].map(base_weight)
E['prod_factors'] = (E['f1_sig'] * E['f2_fund'] * E['f3_val'] * E['f4_vol'] *
                     E['f5_liq'] * E['f6_trend'] * E['f7_regime'] * E['f8_analyst'])
E['pos_conf'] = np.clip(E['base'] * E['prod_factors'], 0.005, 2 * E['base'])

for f, src in [('f2_fund', E['f_fund']), ('f3_val', E['f_val']), ('f4_vol', E['vol60_ann']),
               ('f5_liq', E['turnover_yi']), ('f6_trend', E['adx']), ('f7_regime', E['f_regime'])]:
    print(f"  {f}: raw coverage {src.notna().mean():.1%}")

# position size distribution
print("\npos_conf distribution (>=4 events):")
print(E[E['score'] >= 4]['pos_conf'].describe().round(3).to_string())

# =====================================================================
# 9. Variants
# =====================================================================
EV = E.dropna(subset=['alpha20', 'alpha60']).copy()
EV4 = EV[EV['tier'] == 'ge4'].copy()   # 击球区 events (v3.1 50% first-tranche universe)
EV3 = EV[EV['tier'] == 'ge3'].copy()   # 观察区+击球区 events (v4.0 broader universe)

print(f"\nEV4 (击球区, clustered): {len(EV4)} events | EV3 (观察+击球): {len(EV3)} events")

def pos_for(variant):
    if variant == 'V0_uniform_0pct':
        return np.zeros(len(EV4))
    if variant == 'V1_uniform_50pct':
        return np.full(len(EV4), 0.50)
    if variant == 'V2_uniform_100pct':
        return np.full(len(EV4), 1.00)
    if variant == 'V4_conf_8f_ge4':
        return EV4['pos_conf'].values
    if variant == 'V6_conf_2f_ge4':  # simplified: only f1_sig + f6_trend
        prod2 = EV4['f1_sig'] * EV4['f6_trend']
        return np.clip(EV4['base'] * prod2, 0.005, 2 * EV4['base']).values
    return None

variant_dfs = {}
for vn in ['V0_uniform_0pct', 'V1_uniform_50pct', 'V2_uniform_100pct', 'V4_conf_8f_ge4', 'V6_conf_2f_ge4']:
    sub = EV4.copy()
    sub['pos'] = pos_for(vn)
    sub['variant'] = vn
    variant_dfs[vn] = sub
V3 = EV3.copy()
V3['pos'] = V3['pos_conf']
V3['variant'] = 'V3_conf_8f_ge3'
variant_dfs['V3_conf_8f_ge3'] = V3
# apples-to-apples uniform-50% on the ge3 universe (vs V3)
V5 = EV3.copy()
V5['pos'] = 0.50
V5['variant'] = 'V5_uniform_50pct_ge3'
variant_dfs['V5_uniform_50pct_ge3'] = V5

# =====================================================================
# 10. Event-level metrics
# =====================================================================
def event_metrics(sub, h):
    a = sub[f'alpha{h}'].dropna()
    n = len(a)
    if n == 0:
        return dict(n=0)
    m = {'n': n, 'mean_alpha': float(a.mean()), 'median_alpha': float(a.median()),
         'mean_ret': float(sub[f'r{h}'].dropna().mean()),
         'win_rate': float((a > 0).mean()), 'std_alpha': float(a.std())}
    if n >= 3 and a.std() > 0:
        t, p = stats.ttest_1samp(a, 0)
        m['t'] = round(float(t), 3)
        m['p'] = round(float(p), 4)
    return m

summary_rows = []
for h in ['20', '60']:
    for vn, sub in variant_dfs.items():
        m = event_metrics(sub, h)
        m['variant'], m['horizon'] = vn, h
        summary_rows.append(m)
summary = pd.DataFrame(summary_rows)
summary.to_csv(f'{OUT}/bt017_summary.csv', index=False)
print("\n=== Event-level summary (alpha = excess vs same-pool bench) ===")
print(summary[['variant', 'horizon', 'n', 'mean_alpha', 'median_alpha', 'win_rate', 't', 'p']].to_string(index=False))

# size-weighted alpha (position size as weight)
w_rows = []
for h in ['20', '60']:
    for vn, sub in variant_dfs.items():
        a = sub[['pos', f'alpha{h}']].dropna()
        n = len(a)
        if n == 0 or a['pos'].sum() == 0:
            continue
        wm = float((a['pos'] * a[f'alpha{h}']).sum() / a['pos'].sum())
        um = float(a[f'alpha{h}'].mean())
        w_rows.append({'variant': vn, 'horizon': h, 'n': n,
                       'size_weighted_alpha': round(wm, 5), 'equal_weight_alpha': round(um, 5),
                       'delta': round(wm - um, 5)})
wdf = pd.DataFrame(w_rows)
wdf.to_csv(f'{OUT}/bt017_weighted_alpha.csv', index=False)
print("\n=== Size-weighted vs equal-weighted alpha (delta>0 => sizing concentrates on better events) ===")
print(wdf.to_string(index=False))

# Bootstrap CI: is size-weighted alpha of V4 vs equal-weight (V1 proxy) significantly different?
rng = np.random.default_rng(42)
boot_rows = []
for h in ['20', '60']:
    sub = EV4[['pos_conf', f'alpha{h}']].dropna()
    n = len(sub)
    sw = sub['pos_conf'].values
    al = sub[f'alpha{h}'].values
    obs_delta = float((sw * al).sum() / sw.sum() - al.mean())
    deltas = []
    for _ in range(2000):
        idx = rng.integers(0, n, n)
        sw_b, al_b = sw[idx], al[idx]
        if sw_b.sum() == 0:
            continue
        deltas.append(float((sw_b * al_b).sum() / sw_b.sum() - al_b.mean()))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    boot_rows.append({'horizon': h, 'n': n, 'obs_delta_sw_vs_eq': round(obs_delta, 5),
                      'ci_lo_2.5': round(lo, 5), 'ci_hi_97.5': round(hi, 5),
                      'pct_gt_0': round(float((np.array(deltas) > 0).mean()), 3)})
bootdf = pd.DataFrame(boot_rows)
bootdf.to_csv(f'{OUT}/bt017_bootstrap_delta.csv', index=False)
print("\n=== Bootstrap 95% CI of (size-weighted alpha - equal-weight alpha), V4 on ge4 ===")
print(bootdf.to_string(index=False))

# Bootstrap for V6 (simplified 2-factor) — does IT concentrate on better events?
prod2 = EV4['f1_sig'] * EV4['f6_trend']
pos6 = np.clip(EV4['base'] * prod2, 0.005, 2 * EV4['base']).values
boot6_rows = []
for h in ['20', '60']:
    sub = EV4[[f'alpha{h}']].dropna()
    n = len(sub)
    sw6 = pos6[:n]
    al = sub[f'alpha{h}'].values
    obs_delta = float((sw6 * al).sum() / sw6.sum() - al.mean())
    deltas = []
    for _ in range(2000):
        idx = rng.integers(0, n, n)
        sw_b, al_b = sw6[idx], al[idx]
        if sw_b.sum() == 0:
            continue
        deltas.append(float((sw_b * al_b).sum() / sw_b.sum() - al_b.mean()))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    boot6_rows.append({'horizon': h, 'n': n, 'obs_delta_sw_vs_eq': round(obs_delta, 5),
                       'ci_lo_2.5': round(lo, 5), 'ci_hi_97.5': round(hi, 5),
                       'pct_gt_0': round(float((np.array(deltas) > 0).mean()), 3)})
boot6df = pd.DataFrame(boot6_rows)
boot6df.to_csv(f'{OUT}/bt017_bootstrap_delta_v6.csv', index=False)
print("\n=== Bootstrap 95% CI of (size-weighted alpha - equal-weight alpha), V6 (2-factor) on ge4 ===")
print(boot6df.to_string(index=False))

# =====================================================================
# 11. Portfolio simulation — mark-to-market, no leverage, pro-rata scaling
# =====================================================================
def portfolio_sim(events_df, hold=60):
    """events_df: code/date/pos. Enters at close of event date, holds `hold`
    trading days (by row position). Concurrent positions pro-rata scaled so
    total exposure <= 100% NAV. Returns (nav_series, trade_stats)."""
    # build a global trading calendar = sorted union of all pool dates in window
    all_dates = sorted(set().union(*[set(d.index) for d in price_dfs.values()]))
    all_dates = pd.DatetimeIndex(all_dates)
    # precompute per-code close series and position index
    evs = events_df.dropna(subset=['pos']).copy()
    trades = []
    for _, e in evs.iterrows():
        code, date, pos = e['code'], e['date'], float(e['pos'])
        if code not in price_dfs:
            continue
        c = price_dfs[code]['close']
        if date not in c.index:
            continue
        loc = c.index.get_loc(date)
        if loc + 1 >= len(c):
            continue
        entry = float(c.iloc[loc])
        end_loc = min(loc + hold, len(c) - 1)
        trades.append({'code': code, 'entry_date': date, 'exit_date': c.index[end_loc],
                       'pos': pos, 'entry': entry})
    if not trades:
        return pd.Series(dtype=float), pd.DataFrame()
    tr = pd.DataFrame(trades)
    tr['entry_date'] = pd.to_datetime(tr['entry_date'])
    tr['exit_date'] = pd.to_datetime(tr['exit_date'])

    # map each date to global calendar position
    cal = {d: i for i, d in enumerate(all_dates)}
    entry_loc = tr['entry_date'].map(cal)
    exit_loc = tr['exit_date'].map(cal)
    n_days = len(all_dates)
    nav = np.ones(n_days)
    # iterate day by day, managing open positions
    open_pos = []  # list of dicts: code, exit_idx, raw_pos, prev_price, first_day
    for i in range(n_days):
        day = all_dates[i]
        # enter new positions today (at today's close = prev close for first daily ret)
        todays = tr[entry_loc == i]
        for _, t in todays.iterrows():
            c = price_dfs[t['code']]['close']
            entry_px = float(c.loc[t['entry_date']]) if t['entry_date'] in c.index else t['entry']
            open_pos.append({'code': t['code'], 'exit_idx': exit_loc[t.name],
                             'raw_pos': t['pos'], 'prev': entry_px})
        # liquidate expired (positions whose hold window ended yesterday)
        open_pos = [p for p in open_pos if p['exit_idx'] >= i]
        if not open_pos:
            nav[i] = nav[i - 1] if i > 0 else 1.0
            continue
        # day-over-day returns for open positions
        rets = []
        for p in open_pos:
            c = price_dfs[p['code']]['close']
            if day in c.index:
                cur = float(c.loc[day])
            else:
                prev = c.index[c.index <= day]
                cur = float(c.loc[prev[-1]]) if len(prev) else p['prev']
            rets.append(cur / p['prev'] - 1)
            p['prev'] = cur
        raw_w = np.array([p['raw_pos'] for p in open_pos])
        total_w = raw_w.sum()
        if total_w > 1.0:
            w = raw_w / total_w  # pro-rata scale to 100%
        else:
            w = raw_w
        port_ret = float(np.dot(w, rets))
        nav[i] = nav[i - 1] * (1 + port_ret) if i > 0 else 1.0 + port_ret
    nav_series = pd.Series(nav, index=all_dates)
    return nav_series, tr

port_rows = []
for h in [20, 60]:
    for vn, sub in variant_dfs.items():
        nav, tr = portfolio_sim(sub, hold=h)
        if len(nav) < 30:
            continue
        rets = nav.pct_change().dropna()
        ann_sharpe = float(rets.mean() / rets.std() * np.sqrt(252)) if rets.std() > 0 else np.nan
        mdd = float((nav / nav.cummax() - 1).min())
        total = float(nav.iloc[-1] / nav.iloc[0] - 1)
        port_rows.append({'variant': vn, 'hold': h, 'n_trades': int(len(tr)),
                          'ann_sharpe': round(ann_sharpe, 3), 'max_dd': round(mdd, 4),
                          'total_ret': round(total, 4), 'nav_end': round(float(nav.iloc[-1]), 4)})
port = pd.DataFrame(port_rows)
port.to_csv(f'{OUT}/bt017_portfolio.csv', index=False)
print("\n=== Portfolio sim (mark-to-market, no leverage, pro-rata 100% cap) ===")
print(port.to_string(index=False))

# =====================================================================
# 12. Per-factor OAT (neutralize one factor at a time; measure size-weighted alpha)
# =====================================================================
oat_rows = []
base_factors = ['f1_sig', 'f2_fund', 'f3_val', 'f4_vol', 'f5_liq', 'f6_trend', 'f7_regime']
for h in ['20', '60']:
    full = EV4.copy()
    a = full[[f'alpha{h}', 'pos_conf']].dropna()
    ref_wm = float((a['pos_conf'] * a[f'alpha{h}']).sum() / a['pos_conf'].sum())
    for fcol in base_factors:
        tmp = full.copy()
        tmp['prod_no'] = tmp['prod_factors'] / tmp[fcol].replace(0, np.nan)
        tmp['pos_no'] = np.clip(tmp['base'] * tmp['prod_no'], 0.005, 2 * tmp['base'])
        an = tmp[[f'alpha{h}', 'pos_no']].dropna()
        wm_no = float((an['pos_no'] * an[f'alpha{h}']).sum() / an['pos_no'].sum())
        oat_rows.append({'horizon': h, 'factor_neutralized': fcol,
                         'full_sw_alpha': round(ref_wm, 5), 'neutral_sw_alpha': round(wm_no, 5),
                         'delta': round(wm_no - ref_wm, 5),
                         'note': 'delta<0 => factor ADDS value (neutralizing lowers sw-alpha)'})
oat = pd.DataFrame(oat_rows)
oat.to_csv(f'{OUT}/bt017_factor_oats.csv', index=False)
print("\n=== Per-factor OAT on >=4 events (neutralize -> watch size-weighted alpha) ===")
print(oat.to_string(index=False))

# =====================================================================
# 13. Robustness: year split + cap/floor grid
# =====================================================================
rob_rows = []
for year in [2025, 2026]:
    for vn, sub in variant_dfs.items():
        ysub = sub[sub['date'].dt.year == year]
        for h in ['20', '60']:
            m = event_metrics(ysub, h)
            m.update({'variant': vn, 'year': year, 'horizon': h})
            rob_rows.append(m)
rob = pd.DataFrame(rob_rows)
rob.to_csv(f'{OUT}/bt017_sensitivity.csv', index=False)
print("\n=== Year split (2025 vs 2026), mean_alpha ===")
print(rob[rob['horizon'] == '60'][['variant', 'year', 'n', 'mean_alpha', 'win_rate']].to_string(index=False))

sens = []
for cap_mult in [1.5, 2.0, 3.0, 4.0]:
    for floor in [0.005, 0.02]:
        tmp = EV4.copy()
        tmp['pos_s'] = np.clip(tmp['base'] * tmp['prod_factors'], floor, cap_mult * tmp['base'])
        for h in ['20', '60']:
            a = tmp[[f'alpha{h}', 'pos_s']].dropna()
            if len(a) == 0 or a['pos_s'].sum() == 0:
                continue
            wm = float((a['pos_s'] * a[f'alpha{h}']).sum() / a['pos_s'].sum())
            sens.append({'cap_mult': cap_mult, 'floor': floor, 'horizon': h,
                         'size_weighted_alpha': round(wm, 5)})
sensdf = pd.DataFrame(sens)
sensdf.to_csv(f'{OUT}/bt017_capfloor_sens.csv', index=False)
print("\n=== Cap/floor sensitivity (>=4 events, size-weighted alpha) ===")
print(sensdf.pivot_table(index='cap_mult', columns=['floor', 'horizon'], values='size_weighted_alpha').to_string())

# =====================================================================
# 14. Summary json
# =====================================================================
res = {
    'events': {'clustered_ge3': int(len(EV3)), 'clustered_ge4': int(len(EV4)),
               'raw_ge4': int((df['score'] >= 4).sum()), 'raw_ge3': int((df['score'] >= 3).sum())},
    'factor_coverage': {f: round(float(E[f].notna().mean()), 3)
                        for f in ['f2_fund', 'f3_val', 'f4_vol', 'f5_liq', 'f6_trend', 'f7_regime']},
    'notes': ['f8 analyst=1.0 constant (discretionary overlay, not backtestable)',
              'regime = CSI300 ETF MA60 single proxy (MCI/国家队 not backtestable as series)',
              'PB percentile = trailing 252d PIT; ROE/debt = latest FY annual by Apr30 deadline',
              'event cluster = first score>=3 per code per 60-trading-day window'],
}
with open(f'{OUT}/summary.json', 'w') as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)

E.to_csv(f'{OUT}/bt017_events.csv', index=False)
print("\nDone. outputs ->", OUT)
