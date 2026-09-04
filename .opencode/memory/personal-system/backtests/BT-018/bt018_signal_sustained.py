#!/usr/bin/env python3
"""
BT-018 — "信号持续期持有口径" confidence-scaled sizing vs uniform 50%
(BUY_LADDER v3.1 actual intended usage)

Research-only. NO trading.

Question (follow-up to BT-017): BT-017 tested "first-entry event then fixed
20/60d hold" and found the full 8-factor confidence model does NOT beat uniform
50%. Its Why5 weakness: v3.1's ACTUAL intended usage is "enter when score
crosses >= thr, HOLD while the signal persists, exit when it dies". BT-016's
+1.26% alpha60 lives exactly in that sustained-holding caliber (repeat events).
Does confidence-scaled sizing beat uniform 50% UNDER THE SUSTAINED-HOLDING
caliber?

Caliber (v3.1 literal reading):
  entry = score (W_B: 2*tb + 2*zoo + 1*candle + 1*adline, max 6) crosses >= thr
          from below, on a day with no active sell flag (end_count == 0)
  hold  = while score >= thr AND end_count == 0
  exit  = score falls below thr OR end_count >= 1 OR data ends

Variants (sizing set at ENTRY, held constant during episode):
  V1  uniform 50% per position           (v3.1 baseline)
  V4  confidence-scaled, BT-017 8-factor model (base * prod f1..f8, clip floor 0.5%, cap 2x base)
  V6  simplified 2-factor (f1_sig * f6_trend)
  V6b variants: no-floor/cap, cap 1.5x, floor 2%
  Threshold >=3 (观察区) and >=4 (击球区) both tested.

Portfolio sim (episode-based, mark-to-market, no leverage):
  - each episode opens a position sized w_entry * NAV at entry close
  - concurrent positions' weights pro-rata scaled so total exposure <= 100%
  - Convention A: exit at close of last lit day (BT-017-style, 1-day episodes -> 0)
  - Convention B: exit at close of day AFTER last lit day (realistic T+1 action on
    signal death; 1-day episodes capture the next-day move)

Outputs -> results/ CSVs + summary.json
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
FUND_RAW = f'{ROOT}/.opencode/memory/personal-system/backtests/BT-017/results/fundamentals_raw.json'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(OUT, exist_ok=True)

pool = json.load(open(POOL))
codes = [p['code'] for p in pool]
fund_raw = json.load(open(FUND_RAW))

# =====================================================================
# 0. Load cache, compute score (BT-016 W_B)
# =====================================================================
df = pd.read_parquet(CACHE)
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
W = {'technical_basic': 2, 'alpha_zoo': 2, 'candlestick': 1, 'ad_line': 1}
df['score'] = sum(df[k].gt(0).astype(int) * w for k, w in W.items())
df = df.sort_values(['code', 'date']).reset_index(drop=True)
print(f"cache {df.shape} | score>=3: {(df['score']>=3).sum()} | >=4: {(df['score']>=4).sum()} | end_count>=1: {(df['end_count']>=1).sum()}")

# =====================================================================
# 1. Load daily prices + per-code features (reuse BT-017 implementations)
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
# 2. Fundamentals PIT (reuse BT-017)
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
# 3. Regime proxy (CSI300 ETF MA60)
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
# 4. Factor functions (reuse BT-017)
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

def base_weight(sc):
    return 0.30 if sc == 3 else 0.50

def pos_conf_for(row):
    prod = (row['f1_sig'] * row['f2_fund'] * row['f3_val'] * row['f4_vol'] *
            row['f5_liq'] * row['f6_trend'] * row['f7_regime'] * row['f8_analyst'])
    return float(np.clip(row['base'] * prod, 0.005, 2 * row['base']))

def pos6_for(row):
    prod2 = row['f1_sig'] * row['f6_trend']
    return float(np.clip(row['base'] * prod2, 0.005, 2 * row['base']))

# =====================================================================
# 5. Episode engine — signal-sustained holding state machine
# =====================================================================
# exit rules:
#   'both'     : exit when score<thr OR end_count>=1   (v3.1 literal, primary)
#   'score_only': exit when score<thr                   (end_count ignored)
#   'sticky'   : exit when score<2 AND end_count==0     (stickier score)
def build_episodes(thr, exit_rule='both'):
    """Returns list of (code, entry_date, exit_date_last_lit, score_at_entry)."""
    eps = []
    for code, g in df.groupby('code'):
        dates = g['date'].values
        sc = g['score'].values
        ec = g['end_count'].values
        lit = sc >= thr
        if exit_rule == 'both':
            active = lit & (ec == 0)
        elif exit_rule == 'score_only':
            active = lit
        elif exit_rule == 'sticky':
            active = (sc >= 2) & (ec == 0)
        else:
            raise ValueError(exit_rule)
        n = len(g)
        i = 0
        while i < n:
            if active[i]:
                j = i
                while j + 1 < n and active[j + 1]:
                    j += 1
                # episode [i, j] on the per-code calendar
                eps.append({'code': code, 'entry_date': pd.Timestamp(dates[i]),
                            'exit_date': pd.Timestamp(dates[j]),
                            'score': int(sc[i])})
                i = j + 1
            else:
                i += 1
    return eps

# =====================================================================
# 6. Global calendar + per-code close alignment
# =====================================================================
all_dates = sorted(set().union(*[set(d.index) for d in price_dfs.values()]))
all_dates = pd.DatetimeIndex(all_dates)
cal_idx = {d: i for i, d in enumerate(all_dates)}
n_days = len(all_dates)

# forward-filled close matrix (code x date)
close_df = pd.DataFrame(index=all_dates, columns=sorted(price_dfs.keys()), dtype=float)
for c, d in price_dfs.items():
    close_df[c] = d['close']
close_ff = close_df.ffill()
# daily returns (per code)
ret_df = close_ff.pct_change()

# log-price matrix for cross-sectional benchmark (BT-016 convention: mean of
# SAME-HORIZON log returns over the pool — NOT compounded daily-mean, which
# over-weights limit-up movers each day and biases the benchmark upward)
log_price = np.log(close_ff.replace(0, np.nan))
log_price = log_price.ffill()
ret_df = log_price.diff()

# =====================================================================
# 7. Episode table with entry-date factors + position sizes
# =====================================================================
def make_episode_table(thr, exit_rule='both'):
    eps = build_episodes(thr, exit_rule)
    rows = []
    for e in eps:
        code, date = e['code'], e['entry_date']
        if code not in price_dfs or date not in close_ff.index:
            continue
        row = {'code': code, 'entry_date': date, 'exit_date': e['exit_date'],
               'score': e['score']}
        feats = feat_cache.get(code)
        row['vol60_ann'] = row['turnover_yi'] = row['adx'] = row['wt1'] = np.nan
        if feats is not None and date in feats.index:
            f = feats.loc[date]
            for k in ['vol60_ann', 'turnover_yi', 'adx', 'wt1']:
                v = f[k]
                row[k] = np.nan if pd.isna(v) else float(v)
        ff, fv = fund_factors(code, date)
        row['f_fund'] = ff if ff is not None else 1.0
        row['f_val'] = fv if fv is not None else 1.0
        row['f_regime'] = regime_factor(date)
        row['f1_sig'] = f_signal(row['score'])
        row['f2_fund'] = row['f_fund']
        row['f3_val'] = row['f_val']
        row['f4_vol'] = f_vol(row['vol60_ann'])
        row['f5_liq'] = f_liq(row['turnover_yi'])
        row['f6_trend'] = f_trend(row['adx'], row['wt1'])
        row['f7_regime'] = row['f_regime']
        row['f8_analyst'] = 1.0
        row['base'] = base_weight(row['score'])
        # positions
        row['pos_v1'] = 0.50 if row['score'] >= 4 else (0.50 if row['score'] >= 3 else 0.30)
        # V1 uniform 50%: base v3.1 first tranche on >=4; for >=3 universe use 0.50 as well (V5-style)
        row['pos_v1'] = 0.50
        row['pos_v4'] = pos_conf_for(row)
        row['pos_v6'] = pos6_for(row)
        p6 = row['base'] * row['f1_sig'] * row['f6_trend']
        row['pos_v6b_nocap'] = float(p6)                       # no floor/cap
        row['pos_v6b_cap15'] = float(np.clip(p6, 0.005, 1.5 * row['base']))
        row['pos_v6b_flo20'] = float(np.clip(p6, 0.02, 2 * row['base']))
        rows.append(row)
    T = pd.DataFrame(rows)
    if len(T):
        T['entry_idx'] = T['entry_date'].map(cal_idx)
        T['exit_idx'] = T['exit_date'].map(cal_idx)
    return T

# =====================================================================
# 8. Portfolio simulation (episode-based, pro-rata cap, both conventions)
# =====================================================================
def portfolio_sim(T, conv='B'):
    """Episode positions. conv A: exit at close of last lit day (exit_idx).
    conv B: exit at close of day after last lit day (exit_idx+1, capped at n_days-1)."""
    if len(T) == 0:
        return pd.Series(dtype=float), {}
    entry_idx = T['entry_idx'].values
    exit_idx = T['exit_idx'].values.copy()
    if conv == 'B':
        exit_idx = np.minimum(exit_idx + 1, n_days - 1)
    # position held from close of entry day through close of exit day:
    # return = P[exit]/P[entry] - 1, realized over days entry..exit
    nav = np.ones(n_days)
    # build per-day open lists: for each day i, positions with entry_idx<=i<=exit_idx
    open_by_day = [[] for _ in range(n_days)]
    for t in range(len(T)):
        code = T['code'].iloc[t]
        w = T['pos'].iloc[t]
        for i in range(int(entry_idx[t]), int(exit_idx[t]) + 1):
            open_by_day[i].append((code, w, t))
    n_pos_hist = []
    for i in range(n_days):
        day = all_dates[i]
        o = open_by_day[i]
        n_pos_hist.append(len(o))
        if not o:
            nav[i] = nav[i - 1] if i > 0 else 1.0
            continue
        rets = []
        for code, w, t in o:
            # day return from prev day close to today close (forward-filled)
            px = close_ff[code]
            if day in px.index:
                cur = float(px.loc[day])
            else:
                prev = px.index[px.index <= day]
                cur = float(px.loc[prev[-1]]) if len(prev) else float(px.iloc[0])
            # entry reference: close of entry day (already in px via ff)
            ent = float(px.iloc[int(entry_idx[t])])
            # daily ret from yesterday
            if i > int(entry_idx[t]):
                prev_px = float(px.iloc[i - 1]) if i - 1 >= 0 else ent
                r = cur / prev_px - 1.0
            else:
                r = 0.0  # day of entry: no return (entered at close)
            rets.append(r)
        raw_w = np.array([o[k][1] for k in range(len(o))])
        total_w = raw_w.sum()
        w = raw_w / total_w if total_w > 1.0 else raw_w
        port_ret = float(np.dot(w, rets))
        nav[i] = nav[i - 1] * (1 + port_ret) if i > 0 else 1.0 + port_ret
    nav_series = pd.Series(nav, index=all_dates)
    # stats over cache window only
    w0 = pd.Timestamp('2024-10-08'); w1 = pd.Timestamp('2026-08-13')
    mask = (all_dates >= w0) & (all_dates <= w1)
    nph = np.array(n_pos_hist)[mask]
    stats_d = {'avg_n_pos': float(np.mean(nph)),
               'max_n_pos': int(np.max(nph)) if len(nph) else 0}
    return nav_series, stats_d

def portfolio_metrics(nav):
    # evaluate only over the cache window (2024-10-08 .. 2026-08-13) —
    # price history before the signal cache starts must not deflate Sharpe/return
    w0 = pd.Timestamp('2024-10-08'); w1 = pd.Timestamp('2026-08-13')
    nav = nav[(nav.index >= w0) & (nav.index <= w1)]
    rets = nav.pct_change().dropna()
    if len(rets) < 30 or rets.std() == 0:
        return {'ann_sharpe': np.nan, 'max_dd': np.nan, 'total_ret': np.nan, 'n_days': int(len(nav))}
    ann_sharpe = float(rets.mean() / rets.std() * np.sqrt(252))
    mdd = float((nav / nav.cummax() - 1).min())
    total = float(nav.iloc[-1] / nav.iloc[0] - 1)
    return {'ann_sharpe': round(ann_sharpe, 3), 'max_dd': round(mdd, 4),
            'total_ret': round(total, 4), 'n_days': int(len(nav))}

def yearly_metrics(nav):
    w0 = pd.Timestamp('2024-10-08'); w1 = pd.Timestamp('2026-08-13')
    nav = nav[(nav.index >= w0) & (nav.index <= w1)]
    rets = nav.pct_change().dropna()
    out = {}
    for yr in [2025, 2026]:
        r = rets[rets.index.year == yr]
        if len(r) < 20:
            continue
        out[yr] = {'ret': round(float(r.sum()), 4),
                   'sharpe': round(float(r.mean() / r.std() * np.sqrt(252)), 3) if r.std() > 0 else np.nan,
                   'n_days': int(len(r))}
    return out

# =====================================================================
# 9. Episode-level alpha + bootstrap (sizing effect isolation)
# =====================================================================
def episode_alpha(T):
    """episode log return minus BT-016-style cross-sectional benchmark:
    mean over pool codes of log returns over the SAME window [i0, i1].
    Window = conv-B [entry_idx, exit_idx+1] to match the primary portfolio."""
    L = log_price.values  # n_days x n_codes
    a = []
    for _, r in T.iterrows():
        i0, i1 = int(r['entry_idx']), min(int(r['exit_idx']) + 1, n_days - 1)
        if i1 < i0:
            i1 = i0
        code = r['code']
        col = log_price.columns.get_loc(code)
        p0 = L[i0, col]; p1 = L[i1, col]
        if not np.isfinite(p0) or not np.isfinite(p1):
            a.append(np.nan); continue
        ep_ret = p1 - p0
        # same-window pool benchmark: mean of log returns across codes
        b_ret = float(np.nanmean(L[i1, :] - L[i0, :]))
        a.append(ep_ret - b_ret)
    T['ep_alpha'] = a
    return T

def bootstrap_delta(T, pos_col, seed=42, n_iter=2000):
    """Bootstrap distribution of (size-weighted ep_alpha - equal-weight ep_alpha)."""
    sub = T[['ep_alpha', pos_col]].dropna()
    if len(sub) < 10:
        return {}
    rng = np.random.default_rng(seed)
    sw = sub[pos_col].values
    al = sub['ep_alpha'].values
    obs = float((sw * al).sum() / sw.sum() - al.mean())
    deltas = []
    for _ in range(n_iter):
        idx = rng.integers(0, len(sub), len(sub))
        sw_b, al_b = sw[idx], al[idx]
        if sw_b.sum() == 0:
            continue
        deltas.append(float((sw_b * al_b).sum() / sw_b.sum() - al_b.mean()))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    return {'n': int(len(sub)), 'obs_delta_sw_vs_eq': round(obs, 5),
            'ci_lo_2.5': round(lo, 5), 'ci_hi_97.5': round(hi, 5),
            'pct_gt_0': round(float((np.array(deltas) > 0).mean()), 3)}

# =====================================================================
# 10. RUN
# =====================================================================
THRESHOLDS = [3, 4]
EXIT_RULES = ['both', 'score_only', 'sticky']
POS_VARIANTS = {
    'V1_uniform_50pct': 'pos_v1',
    'V4_conf_8f': 'pos_v4',
    'V6_conf_2f': 'pos_v6',
    'V6b_nocap_2f': 'pos_v6b_nocap',
    'V6b_cap15_2f': 'pos_v6b_cap15',
    'V6b_flo20_2f': 'pos_v6b_flo20',
}
PRIMARY_THR, PRIMARY_EXIT = 4, 'both'

# ---- primary run: thr=4, exit='both' ----
T0 = make_episode_table(PRIMARY_THR, PRIMARY_EXIT)
print(f"\n=== PRIMARY: thr={PRIMARY_THR}, exit={PRIMARY_EXIT} -> {len(T0)} episodes ===")
ep_len = T0['exit_idx'] - T0['entry_idx'] + 1
print(f"episode length: mean={ep_len.mean():.2f} med={ep_len.median():.0f} | 1-day: {(ep_len==1).mean():.1%} | max={ep_len.max()}")
T0 = episode_alpha(T0)

# episode alpha decomposition: first-day vs rest
L = log_price.values
first_alpha, rest_alpha = [], []
for _, r in T0.iterrows():
    i0 = int(r['entry_idx'])
    col = log_price.columns.get_loc(r['code'])
    if i0 + 1 >= n_days:
        continue
    p0 = L[i0, col]; p1 = L[i0 + 1, col]
    if np.isfinite(p0) and np.isfinite(p1) and not np.isnan(r['ep_alpha']):
        # first-day log return vs same-day pool mean
        b_first = float(np.nanmean(L[i0 + 1, :] - L[i0, :]))
        first_alpha.append((p1 - p0) - b_first)
        rest_alpha.append(r['ep_alpha'] - first_alpha[-1])
first_alpha = np.array(first_alpha); rest_alpha = np.array(rest_alpha)
dec_rows = [{'component': 'first_day', 'n': len(first_alpha), 'mean_alpha': round(float(first_alpha.mean()), 5),
             'win_rate': round(float((first_alpha > 0).mean()), 3)},
            {'component': 'rest_of_episode', 'n': len(rest_alpha), 'mean_alpha': round(float(rest_alpha.mean()), 5),
             'win_rate': round(float((rest_alpha > 0).mean()), 3)},
            {'component': 'full_episode', 'n': int(T0['ep_alpha'].notna().sum()),
             'mean_alpha': round(float(T0['ep_alpha'].mean()), 5),
             'win_rate': round(float((T0['ep_alpha'] > 0).mean()), 3)}]
pd.DataFrame(dec_rows).to_csv(f'{OUT}/bt018_episode_decomposition.csv', index=False)
print("\n=== Episode alpha decomposition (sustained-holding) ===")
print(pd.DataFrame(dec_rows).to_string(index=False))
t_ep = stats.ttest_1samp(T0['ep_alpha'].dropna(), 0)
print(f"full-episode alpha: t={t_ep.statistic:.2f}, p={t_ep.pvalue:.4f}")

# ---- portfolio sim per variant (primary thr/exit), conv A and B ----
port_rows = []
for conv in ['A', 'B']:
    for vn, col in POS_VARIANTS.items():
        sub = T0.copy()
        sub['pos'] = sub[col]
        nav, pstat = portfolio_sim(sub, conv=conv)
        m = portfolio_metrics(nav)
        m.update({'variant': vn, 'conv': conv, 'exit': PRIMARY_EXIT, 'thr': PRIMARY_THR,
                  'n_episodes': int(len(sub)), 'avg_n_pos': pstat.get('avg_n_pos'),
                  'max_n_pos': pstat.get('max_n_pos')})
        ym = yearly_metrics(nav)
        m['ret_2025'] = ym.get(2025, {}).get('ret')
        m['sharpe_2025'] = ym.get(2025, {}).get('sharpe')
        m['ret_2026'] = ym.get(2026, {}).get('ret')
        m['sharpe_2026'] = ym.get(2026, {}).get('sharpe')
        port_rows.append(m)
        nav.to_csv(f'{OUT}/bt018_nav_{vn}_thr{PRIMARY_THR}_{PRIMARY_EXIT}_conv{conv}.csv')
port = pd.DataFrame(port_rows)
port.to_csv(f'{OUT}/bt018_portfolio.csv', index=False)
print("\n=== Portfolio sim (thr=4, exit='both') ===")
print(port[['variant', 'conv', 'ann_sharpe', 'max_dd', 'total_ret', 'n_episodes', 'avg_n_pos']].to_string(index=False))

# ---- bootstrap sizing-effect per variant (episode-level, conv-B window) ----
boot_rows = []
for vn, col in POS_VARIANTS.items():
    b = bootstrap_delta(T0, col)
    b.update({'variant': vn})
    boot_rows.append(b)
bootdf = pd.DataFrame(boot_rows)
bootdf.to_csv(f'{OUT}/bt018_bootstrap_delta.csv', index=False)
print("\n=== Bootstrap (size-weighted - equal-weighted) episode alpha, thr=4 ===")
print(bootdf.to_string(index=False))

# ---- caliber comparison: where does the alpha live? (bridges BT-016/BT-017) ----
# From each ACTIVE lit day (score>=4, end_count==0): forward alpha over
#   (a) remaining lit window, (b) 20d, (c) 60d  -- BT-016/BT-017-style cross-sectional bench
calib_rows = []
L = log_price.values
lit_days = df[(df['score'] >= 4) & (df['end_count'] == 0)].copy()
recs = []
for _, e in lit_days.iterrows():
    code, t = e['code'], e['date']
    if code not in log_price.columns or t not in cal_idx:
        continue
    gi = cal_idx[t]
    col = log_price.columns.get_loc(code)
    p0 = L[gi, col]
    if not np.isfinite(p0):
        continue
    # find end of lit run (active = score>=4 & ec==0)
    sub = df[(df['code'] == code) & (df['date'] >= t)].sort_values('date')
    act = ((sub['score'] >= 4) & (sub['end_count'] == 0)).values
    j = 0
    while j + 1 < len(act) and act[j + 1]:
        j += 1
    ej = cal_idx[sub['date'].iloc[j]]
    a_lit = None
    if ej > gi and np.isfinite(L[ej, col]):
        a_lit = (L[ej, col] - p0) - float(np.nanmean(L[ej, :] - L[gi, :]))
    a20 = None; a60 = None
    if gi + 20 < n_days and np.isfinite(L[gi + 20, col]):
        a20 = (L[gi + 20, col] - p0) - float(np.nanmean(L[gi + 20, :] - L[gi, :]))
    if gi + 60 < n_days and np.isfinite(L[gi + 60, col]):
        a60 = (L[gi + 60, col] - p0) - float(np.nanmean(L[gi + 60, :] - L[gi, :]))
    recs.append({'a_lit': a_lit, 'a20': a20, 'a60': a60})
recdf = pd.DataFrame(recs)
from scipy import stats as _st
def _summ(s):
    s = s.dropna()
    if len(s) == 0:
        return {'n': 0}
    t, p = _st.ttest_1samp(s, 0)
    return {'n': int(len(s)), 'mean': round(float(s.mean()), 5),
            'win': round(float((s > 0).mean()), 3), 't': round(float(t), 2), 'p': round(float(p), 4)}
calib_rows = []
for col in ['a_lit', 'a20', 'a60']:
    r = _summ(recdf[col])
    r.update({'caliber': {'a_lit': 'lit-window-only (BT-018 sustained)',
                          'a20': '20d-forward (BT-016-style)',
                          'a60': '60d-forward (BT-016-style)'}[col]})
    calib_rows.append(r)
calibdf = pd.DataFrame(calib_rows)
calibdf.to_csv(f'{OUT}/bt018_caliber_alpha.csv', index=False)
print("\n=== Caliber comparison — alpha from active lit days by measurement window ===")
print(calibdf.to_string(index=False))
print("NOTE: sustained-holding (lit window) alpha ~ 0; BT-016's +1.26% needs the 20-60d post-signal window (drift AFTER signal death).")

# ---- entry-day vs mid-run split: what does BUYING AT THE CROSSING capture? ----
# for each episode: alpha from entry to last lit day (no death day) — the literal
# v3.1 'buy at crossing, hold while lit' P&L; split into mid-run continuation
L = log_price.values
entry_lit_alpha = []
midrun_alpha = []
for _, r in T0.iterrows():
    gi = int(r['entry_idx']); ej = int(r['exit_idx'])
    col = log_price.columns.get_loc(r['code'])
    p0 = L[gi, col]; p1 = L[ej, col]
    if not np.isfinite(p0) or not np.isfinite(p1):
        continue
    a_hold = (p1 - p0) - float(np.nanmean(L[ej, :] - L[gi, :]))
    entry_lit_alpha.append(a_hold)
    # mid-run: from entry+1 (if exists and inside run) to last lit day
    if ej > gi:
        p2 = L[gi + 1, col]
        if np.isfinite(p2):
            midrun_alpha.append(a_hold - ((p2 - p0) - float(np.nanmean(L[gi + 1, :] - L[gi, :]))))
entry_lit_alpha = np.array(entry_lit_alpha)
midrun_alpha = np.array(midrun_alpha)
split_rows = []
for lab, arr in [('entry_to_last_lit_day (v3.1 literal hold)', entry_lit_alpha),
                 ('mid-run continuation (day1+ .. last lit day)', midrun_alpha)]:
    if len(arr) < 5:
        continue
    t, p = stats.ttest_1samp(arr, 0)
    split_rows.append({'component': lab, 'n': int(len(arr)),
                       'mean_alpha': round(float(arr.mean()), 5),
                       'win_rate': round(float((arr > 0).mean()), 3),
                       't': round(float(t), 2), 'p': round(float(p), 4)})
splitdf = pd.DataFrame(split_rows)
splitdf.to_csv(f'{OUT}/bt018_entry_vs_midrun.csv', index=False)
print("\n=== Entry-day vs mid-run split (thr=4, exit=both, no death day) ===")
print(splitdf.to_string(index=False))
print("NOTE: mid-run continuation is the 'repeat-event' edge; buying at the crossing adds it but also pays the entry cost.")

# ---- threshold sensitivity: thr=3, exit='both' ----
T3 = make_episode_table(3, 'both')
print(f"\nthr=3 episodes: {len(T3)}")
T3 = episode_alpha(T3)
ep3_len = T3['exit_idx'] - T3['entry_idx'] + 1
print(f"thr=3 ep length mean={ep3_len.mean():.2f} med={ep3_len.median():.0f}")
sens_rows = []
for conv in ['B']:
    for vn, col in POS_VARIANTS.items():
        sub = T3.copy(); sub['pos'] = sub[col]
        nav, pstat = portfolio_sim(sub, conv=conv)
        m = portfolio_metrics(nav)
        m.update({'variant': vn, 'thr': 3, 'exit': 'both', 'n_episodes': int(len(sub)),
                  'avg_n_pos': pstat.get('avg_n_pos')})
        sens_rows.append(m)
sens = pd.DataFrame(sens_rows)
sens.to_csv(f'{OUT}/bt018_threshold_sens_thr3.csv', index=False)
print("\n=== Threshold sensitivity: thr=3, exit='both', conv B ===")
print(sens[['variant', 'ann_sharpe', 'max_dd', 'total_ret', 'n_episodes', 'avg_n_pos']].to_string(index=False))

# ---- exit-rule sensitivity: thr=4, exit=score_only / sticky ----
exit_sens = []
for er in EXIT_RULES:
    if er == 'both':
        continue
    Te = make_episode_table(4, er)
    Te = episode_alpha(Te)
    for vn, col in POS_VARIANTS.items():
        sub = Te.copy(); sub['pos'] = sub[col]
        nav, pstat = portfolio_sim(sub, conv='B')
        m = portfolio_metrics(nav)
        m.update({'variant': vn, 'thr': 4, 'exit': er, 'n_episodes': int(len(sub)),
                  'avg_n_pos': pstat.get('avg_n_pos')})
        exit_sens.append(m)
exsens = pd.DataFrame(exit_sens)
exsens.to_csv(f'{OUT}/bt018_exit_sensitivity.csv', index=False)
print("\n=== Exit-rule sensitivity: thr=4, conv B ===")
print(exsens[['variant', 'exit', 'ann_sharpe', 'max_dd', 'total_ret', 'n_episodes']].to_string(index=False))

# ---- year-split of PRIMARY (V1 vs V4 vs V6, thr=4, exit=both, conv B) ----
year_rows = []
for vn in ['V1_uniform_50pct', 'V4_conf_8f', 'V6_conf_2f']:
    sub = T0.copy(); sub['pos'] = sub[POS_VARIANTS[vn]]
    nav, _ = portfolio_sim(sub, conv='B')
    ym = yearly_metrics(nav)
    for yr, mm in ym.items():
        year_rows.append({'variant': vn, 'year': yr, **mm})
yrdf = pd.DataFrame(year_rows)
yrdf.to_csv(f'{OUT}/bt018_year_split.csv', index=False)
print("\n=== Year split (primary) ===")
print(yrdf.to_string(index=False))

# ---- per-factor OAT on episodes (neutralize one factor; watch size-weighted ep_alpha) ----
oat_rows = []
fac_cols = ['f1_sig', 'f2_fund', 'f3_val', 'f4_vol', 'f5_liq', 'f6_trend', 'f7_regime']
subE = T0.dropna(subset=['ep_alpha']).copy()
al = subE['ep_alpha'].values
sw_full = subE['pos_v4'].values
ref = float((sw_full * al).sum() / sw_full.sum())
for fcol in fac_cols:
    tmp = subE.copy()
    prod = (tmp['f1_sig'] * tmp['f2_fund'] * tmp['f3_val'] * tmp['f4_vol'] *
            tmp['f5_liq'] * tmp['f6_trend'] * tmp['f7_regime'])
    prod_no = prod / tmp[fcol].replace(0, np.nan)
    pos_no = np.clip(tmp['base'] * prod_no, 0.005, 2 * tmp['base']).values
    sw_no = pos_no
    wm_no = float((sw_no * al).sum() / sw_no.sum())
    oat_rows.append({'factor_neutralized': fcol, 'full_sw_alpha': round(ref, 5),
                     'neutral_sw_alpha': round(wm_no, 5), 'delta': round(wm_no - ref, 5),
                     'note': 'delta<0 => factor ADDS value (neutralizing lowers sw-alpha)'})
oat = pd.DataFrame(oat_rows)
oat.to_csv(f'{OUT}/bt018_factor_oats.csv', index=False)
print("\n=== Per-factor OAT (episode-level, thr=4) ===")
print(oat.to_string(index=False))

# ---- summary json ----
res = {
    'primary': {'thr': PRIMARY_THR, 'exit': PRIMARY_EXIT,
                'n_episodes': int(len(T0)),
                'ep_len_mean': round(float(ep_len.mean()), 2),
                'ep_len_median': int(ep_len.median()),
                'ep_alpha_mean': round(float(T0['ep_alpha'].mean()), 5),
                'ep_alpha_t': round(float(t_ep.statistic), 2),
                'ep_alpha_p': round(float(t_ep.pvalue), 4)},
    'comparison_BT017': {'BT017_first_entry_alpha60_mean': -0.002,
                         'BT017_first_entry_n': 299,
                         'note': 'BT-017 first-entry (60d cluster) alpha60 = -0.20%, ns'},
    'conventions': {'A': 'exit at close of last lit day (1-day eps -> 0 return)',
                    'B': 'exit at close of day after signal death (T+1 action)'},
}
with open(f'{OUT}/summary.json', 'w') as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)

T0.to_csv(f'{OUT}/bt018_episodes.csv', index=False)
print("\nDone. outputs ->", OUT)
