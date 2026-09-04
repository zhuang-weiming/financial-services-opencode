#!/usr/bin/env python3
"""
BT-019 — "V5 观察区(>=3) 20d 短持策略验证" (is the V5 20d edge real, or a 2026 artifact?)

Research-only. NO trading.

Question (from BT-017 finding):
  V5 (uniform 50% position on observation-zone score>=3 events, 20d hold) had the
  HIGHEST 20d portfolio Sharpe in BT-017 (0.839) but collapsed at 60d (0.405).
  Before promoting V5 to a strategy form, validate honestly:
    (1) is the 20d edge robust across 2025 (up) vs 2026 (down)?
    (2) what is the best hold horizon 5/10/20/30/40/60?
    (3) does it survive realistic costs (0.275%/side + T+1)? breakeven cost?
    (4) is it driven by few concentrated events?
    (5) signal-driven or market beta?  -> random-entry control
    (6) hold-until-next-signal variant?

Data (zero new downloads — reuse BT-011 cache):
  - signals: BT-011/results/signal_cache_v2.parquet (16 signals, 200 pool, 2024-10-08..2026-08-13)
  - prices:  data/market/daily/<code>*.csv
  - pool:    BT-011/pool_200.json
  - regime/bench: data/market/daily/510300.csv (CSI300 ETF)

Scoring (BT-016 W_B): score = 2*I(technical_basic>0) + 2*I(alpha_zoo>0)
                            + 1*I(candlestick>0) + 1*I(ad_line>0), max 6
  >=4 -> 击球区, >=3 -> 观察区+击球区. Position 0.50 uniform for both tiers.

Event definition (CORRECTED vs BT-017):
  BT-017 clustered with "gap>=60 in EVENT-INDEX terms" (not trading days) and started
  its NAV at the union-calendar start (~2022-11, ~450 flat pre-sample days). Both
  inflate Sharpe. BT-019 fixes:
  - clustering: first event per code per 60-TRADING-DAY window (BT-017 documented intent)
  - NAV: anchored at active window start (first global trading day >= 2024-10-08)
  - reproduction of BT-017's exact event set + full-calendar NAV is run as a check.

Portfolio sim (mark-to-market, no leverage):
  - entry at close of event day (entry_lag=0) OR close of next trading day (entry_lag=1, T+1 conservative)
  - exit at close of entry+hold (fixed), or next-signal / silence rules (hold-until-signal variants)
  - concurrent positions pro-rata scaled to <=100% NAV
  - costs: cost_per_side applied to entry and exit notional (BT-009 convention 0.275%/side)
  - metrics: annualized Sharpe (active window only), max DD, total return, avg positions, turnover

Benchmarks:
  - uniform 50% at >=4 (BT-016 caliber, same grid)
  - buy-and-hold equal-weight pool average
  - buy-and-hold 510300 (CSI300 ETF)
  - random-entry control (same event count, uniform random entry dates, same holds) x300 reps
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(OUT, exist_ok=True)

COST_SIDE = 0.00275          # BT-009 convention: 0.275%/side (0.55% round trip)
HOLDS = [5, 10, 20, 30, 40, 60]
SAMPLE_START = pd.Timestamp('2024-10-08')
SAMPLE_END = pd.Timestamp('2026-08-13')
W = {'technical_basic': 2, 'alpha_zoo': 2, 'candlestick': 1, 'ad_line': 1}

# =====================================================================
# 0. Load cache + score
# =====================================================================
df = pd.read_parquet(CACHE)
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['score'] = sum(df[k].gt(0).astype(int) * w for k, w in W.items())
print(f"cache {df.shape} | raw score>=3: {(df['score']>=3).sum()} | >=4: {(df['score']>=4).sum()}")

pool = json.load(open(POOL))
codes = [p['code'] for p in pool]

# =====================================================================
# 1. Load daily prices (200 pool only)
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

all_dates = pd.DatetimeIndex(sorted(set().union(*[set(d.index) for d in price_dfs.values()])))
active_dates = all_dates[all_dates >= SAMPLE_START]
print(f"union calendar {len(all_dates)} days | active window {len(active_dates)} days "
      f"({active_dates[0].date()}..{active_dates[-1].date()})")

# =====================================================================
# 2. Events — cluster per code per 60 TRADING DAYS (corrected), tiers ge3 / ge4
#    Also reproduce BT-017 event-index clustering for the 0.839 check.
# =====================================================================
def cluster_td(sub, close_idx, min_gap=60):
    """first event per min_gap trading days on the code's own calendar"""
    keep, last_loc = [], -10**9
    for i in range(len(sub)):
        loc = close_idx.get_loc(sub.index[i]) if sub.index[i] in close_idx else None
        if loc is None:
            continue
        if loc - last_loc >= min_gap:
            keep.append(i)
            last_loc = loc
    return sub.iloc[keep]

def cluster_idx(sub, min_gap=60):
    """BT-017 implementation: gap in EVENT-INDEX terms"""
    keep, last = [], -10**9
    for i in range(len(sub)):
        if i - last >= min_gap:
            keep.append(i)
            last = i
    return sub.iloc[keep]

# raw signal-day index per code (score>=3) for hold-to-signal variants
sig_days = {c: df[df['code'] == c].sort_values('date').set_index('date')
            .query('score >= 3').index for c in codes}

event_rows = []
for c in codes:
    sub = df[df['code'] == c].sort_values('date').set_index('date')
    if len(sub) == 0 or c not in price_dfs:
        continue
    ci = price_dfs[c].index
    for thresh, tier in [(3, 'ge3'), (4, 'ge4')]:
        for clus_name, clus_fn in [('td60', cluster_td), ('idx60', cluster_idx)]:
            ev = clus_fn(sub[sub['score'] >= thresh], ci) if clus_name == 'td60' else clus_fn(sub[sub['score'] >= thresh])
            for i in range(len(ev)):
                row = ev.iloc[i]
                event_rows.append({'code': c, 'date': ev.index[i], 'score': int(row['score']),
                                   'year': int(row['year']), 'tier': tier, 'cluster': clus_name})
E = pd.DataFrame(event_rows)
E['date'] = pd.to_datetime(E['date'])
print("\nevent counts by (cluster, tier):")
print(E.groupby(['cluster', 'tier']).size().to_string())
print(f"total events: {len(E)}")

E0 = E[E['cluster'] == 'td60'].copy()          # primary (corrected)
E_b017 = E[E['cluster'] == 'idx60'].copy()     # BT-017 reproduction

# =====================================================================
# 3. Portfolio sim engine
# =====================================================================
def portfolio_sim(events, hold=20, cost_per_side=0.0, entry_lag=0,
                  exit_rule='fixed', max_hold=None, patience=None,
                  active_start=SAMPLE_START, allow_overlap_code=False):
    """Mark-to-market, no leverage, pro-rata scaling to <=100% NAV.
    Returns (nav_series, stats dict, trades DataFrame)."""
    dates = list(all_dates) if active_start is None else [d for d in all_dates if d >= active_start]
    if not dates:
        return pd.Series(dtype=float), {}, pd.DataFrame()
    cal = {d: i for i, d in enumerate(dates)}
    n_days = len(dates)

    trades = []
    for _, e in events.iterrows():
        code, date = e['code'], e['date']
        pos = float(e.get('pos', 0.5))
        if code not in price_dfs or pos <= 0:
            continue
        c = price_dfs[code]['close']
        if date not in c.index:
            continue
        loc = c.index.get_loc(date) + entry_lag
        if loc >= len(c):
            continue
        entry_day = c.index[loc]
        entry_px = float(c.iloc[loc])
        if exit_rule == 'fixed':
            end_loc = min(loc + hold, len(c) - 1)
            exit_day = c.index[end_loc]
        elif exit_rule == 'next_signal':
            # exit at close of the next score>=3 signal day for this code (capped)
            fut = sig_days.get(code)
            nxt = fut[(fut > entry_day) & (fut <= c.index[min(loc + max_hold, len(c) - 1)])] if fut is not None else []
            exit_day = nxt[0] if len(nxt) else c.index[min(loc + max_hold, len(c) - 1)]
        elif exit_rule == 'silence':
            # exit at close of the first day with no score>=3 signal in trailing `patience` days
            fut = sig_days.get(code)
            end_lim = c.index[min(loc + max_hold, len(c) - 1)]
            exit_day = None
            if fut is not None and len(fut):
                # walk code calendar day by day
                for j in range(loc + 1, min(loc + max_hold, len(c) - 1) + 1):
                    day = c.index[j]
                    lo = day - pd.Timedelta(days=patience * 3)  # generous lookback range
                    recent = fut[(fut <= day) & (fut > day - pd.Timedelta(days=patience * 3))]
                    # count signal within `patience` TRADING days
                    if len(recent):
                        locs = [c.index.get_loc(d) for d in recent if d in c.index]
                        if locs and (j - min(locs) <= patience):
                            continue  # still fresh
                    exit_day = day
                    break
            exit_day = exit_day if exit_day is not None else end_lim
        else:
            raise ValueError(exit_rule)
        if exit_day < entry_day:
            exit_day = entry_day
        trades.append({'code': code, 'entry_date': entry_day, 'exit_date': exit_day,
                       'pos': pos, 'entry': entry_px, 'entry_idx': cal.get(entry_day, -1),
                       'exit_idx': cal.get(exit_day, n_days - 1)})
    if not trades:
        return pd.Series(1.0, index=pd.DatetimeIndex(dates)), {'n_trades': 0}, pd.DataFrame()
    tr = pd.DataFrame(trades)
    tr['entry_idx'] = tr['entry_idx'].clip(0, n_days - 1)
    tr['exit_idx'] = tr['exit_idx'].clip(0, n_days - 1)

    open_pos = []   # dicts: code, exit_idx, raw_pos, prev, last_day
    nav = np.ones(n_days)
    turnover_frac = 0.0
    pos_counts = []
    open_codes = set()
    for i in range(n_days):
        day = dates[i]
        # entries today
        todays = tr[tr['entry_idx'] == i]
        for _, t in todays.iterrows():
            if not allow_overlap_code and t['code'] in open_codes:
                continue
            c = price_dfs[t['code']]['close']
            entry_px = float(c.loc[t['entry_date']]) if t['entry_date'] in c.index else t['entry']
            open_pos.append({'code': t['code'], 'exit_idx': int(t['exit_idx']),
                             'raw_pos': float(t['pos']), 'prev': entry_px})
            open_codes.add(t['code'])
        # expirations (positions whose exit day is today)
        expiring = [p for p in open_pos if p['exit_idx'] == i]
        # day returns for open positions
        if not open_pos:
            if i > 0:
                nav[i] = nav[i - 1]
            pos_counts.append(0)
            continue
        rets, ex_w = [], []
        for p in open_pos:
            c = price_dfs[p['code']]['close']
            if day in c.index:
                cur = float(c.loc[day])
            else:
                prev_ok = c.index[c.index <= day]
                cur = float(c.loc[prev_ok[-1]]) if len(prev_ok) else p['prev']
            rets.append(cur / p['prev'] - 1)
            p['prev'] = cur
            if p in expiring:
                ex_w.append(p['raw_pos'])
        raw_w = np.array([p['raw_pos'] for p in open_pos])
        tot_w = raw_w.sum()
        w = raw_w / tot_w if tot_w > 1.0 else raw_w
        port_ret = float(np.dot(w, rets))
        nav[i] = nav[i - 1] * (1 + port_ret) if i > 0 else 1.0 + port_ret
        # entry cost (notional of today's new entries, at post-return NAV)
        if len(todays):
            new_w = float(todays['pos'].sum())
            if tot_w > 1.0:
                new_w = new_w / tot_w  # pro-rata scaled
            new_w = min(new_w, 1.0)
            if cost_per_side > 0:
                nav[i] *= (1 - cost_per_side * new_w)
            turnover_frac += new_w
        # exit cost
        if expiring:
            ex_tot = float(sum(ex_w))
            if tot_w > 1.0:
                ex_tot = ex_tot / tot_w
            if cost_per_side > 0:
                nav[i] *= (1 - cost_per_side * min(ex_tot, 1.0))
            turnover_frac += ex_tot
        # remove expired
        open_pos = [p for p in open_pos if p['exit_idx'] > i]
        open_codes = {p['code'] for p in open_pos}
        pos_counts.append(len(open_pos))

    nav_s = pd.Series(nav, index=pd.DatetimeIndex(dates))
    n_years = max((dates[-1] - dates[0]).days / 365.25, 1e-6)
    rets = nav_s.pct_change().dropna()
    ann_sharpe = float(rets.mean() / rets.std() * np.sqrt(252)) if rets.std() > 0 else np.nan
    mdd = float((nav_s / nav_s.cummax() - 1).min())
    total = float(nav_s.iloc[-1] / nav_s.iloc[0] - 1)
    stats_out = {
        'n_trades': int(len(tr)),
        'ann_sharpe': round(ann_sharpe, 4),
        'max_dd': round(mdd, 4),
        'total_ret': round(total, 4),
        'avg_positions': round(float(np.mean(pos_counts)), 2) if pos_counts else 0.0,
        'turnover_ann': round(float(turnover_frac / n_years), 2),
    }
    return nav_s, stats_out, tr

def sim_summary_row(tier, hold, cost, lag, nav, st, exit_rule='fixed', tag=''):
    if st.get('n_trades', 0) == 0 or len(nav) < 30:
        return None
    row = {'tier': tier, 'hold': hold, 'cost_per_side': cost, 'entry_lag': lag,
           'exit_rule': exit_rule, **st, 'tag': tag}
    return row

# =====================================================================
# 4. Main grid: tier x hold x {gross, net, net+T1}  (fixed hold, event set td60)
# =====================================================================
rows = []
for tier, thr in [('ge3', 3), ('ge4', 4)]:
    evs = E0[E0['tier'] == tier].copy()
    evs['pos'] = 0.50
    for h in HOLDS:
        # gross
        nav, st, tr = portfolio_sim(evs, hold=h, cost_per_side=0.0, entry_lag=0)
        r = sim_summary_row(tier, h, 0.0, 0, nav, st)
        if r:
            rows.append(r)
        # net (0.275%/side)
        nav, st, tr = portfolio_sim(evs, hold=h, cost_per_side=COST_SIDE, entry_lag=0)
        r = sim_summary_row(tier, h, COST_SIDE, 0, nav, st, tag='net')
        if r:
            rows.append(r)
        # net + T+1 (entry lag 1: buy at next trading day close)
        nav, st, tr = portfolio_sim(evs, hold=h, cost_per_side=COST_SIDE, entry_lag=1)
        r = sim_summary_row(tier, h, COST_SIDE, 1, nav, st, tag='net_t1')
        if r:
            rows.append(r)
grid = pd.DataFrame(rows)
grid.to_csv(f'{OUT}/bt019_grid_fixed_hold.csv', index=False)
print("\n=== MAIN GRID: fixed hold, 50% uniform, tier ge3/ge4 ===")
print(grid[['tier', 'hold', 'tag', 'n_trades', 'ann_sharpe', 'max_dd', 'total_ret',
            'avg_positions', 'turnover_ann']].round(3).to_string(index=False))

# BT-017 reproduction check: idx60 event set + FULL calendar NAV (no active_start)
print("\n=== BT-017 reproduction check (event-index clustering, full-calendar NAV) ===")
rep_rows = []
for tier in ['ge3', 'ge4']:
    evs = E_b017[E_b017['tier'] == tier].copy()
    evs['pos'] = 0.50
    for h in [20, 60]:
        nav, st, tr = portfolio_sim(evs, hold=h, cost_per_side=0.0, entry_lag=0, active_start=None)
        if st.get('n_trades', 0):
            # BT-017 style: full calendar NAV, sharpe on all returns
            rets = nav.pct_change().dropna()
            sh = float(rets.mean() / rets.std() * np.sqrt(252)) if rets.std() > 0 else np.nan
            rep_rows.append({'tier': tier, 'hold': h, 'n_trades': st['n_trades'],
                             'bt017_style_sharpe': round(sh, 3),
                             'active_win_sharpe': st['ann_sharpe']})
rep = pd.DataFrame(rep_rows)
rep.to_csv(f'{OUT}/bt019_bt017_reproduction.csv', index=False)
print(rep.to_string(index=False))

# =====================================================================
# 5. Hold-until-next-signal variants (ge3, entry set td60, hold caps 10/20)
# =====================================================================
sig_rows = []
evs3 = E0[E0['tier'] == 'ge3'].copy()
evs3['pos'] = 0.50
for max_h in [10, 20]:
    for rule in ['next_signal', 'silence']:
        for pat in ([3, 5] if rule == 'silence' else [None]):
            nav, st, tr = portfolio_sim(evs3, hold=max_h, cost_per_side=COST_SIDE,
                                        entry_lag=0, exit_rule=rule, max_hold=max_h, patience=pat)
            r = sim_summary_row('ge3', max_h, COST_SIDE, 0, nav, st, exit_rule=f'{rule}_p{pat}')
            if r:
                sig_rows.append(r)
sig = pd.DataFrame(sig_rows)
sig.to_csv(f'{OUT}/bt019_hold_to_signal.csv', index=False)
print("\n=== HOLD-TO-SIGNAL variants (ge3, net 0.275%/side) ===")
print(sig[['exit_rule', 'hold', 'n_trades', 'ann_sharpe', 'max_dd', 'total_ret',
           'avg_positions', 'turnover_ann']].round(3).to_string(index=False))

# =====================================================================
# 6. Sub-samples: 2025 vs 2026 portfolio sims (ge3, holds 5/20/60, gross+net)
# =====================================================================
sub_rows = []
for year, ystart in [(2024, pd.Timestamp('2024-10-08')), (2025, pd.Timestamp('2025-01-01')),
                     (2026, pd.Timestamp('2026-01-01'))]:
    yev = E0[(E0['tier'] == 'ge3') & (E0['date'].dt.year == year)].copy()
    if not len(yev):
        continue
    yev['pos'] = 0.50
    for h in [5, 20, 60]:
        for cost, tag in [(0.0, 'gross'), (COST_SIDE, 'net')]:
            nav, st, tr = portfolio_sim(yev, hold=h, cost_per_side=cost, entry_lag=0,
                                        active_start=ystart)
            r = sim_summary_row('ge3', h, cost, 0, nav, st, tag=tag)
            if r:
                r['year'] = year
                sub_rows.append(r)
sub = pd.DataFrame(sub_rows)
sub.to_csv(f'{OUT}/bt019_subsample_year.csv', index=False)
print("\n=== SUB-SAMPLE: year-split portfolio sims (ge3, event-year attribution) ===")
print(sub[['year', 'hold', 'tag', 'n_trades', 'ann_sharpe', 'max_dd', 'total_ret']].round(3).to_string(index=False))

# event-level alpha by year (td60 ge3, all holds) — cross-sectional excess vs same-pool bench
# build forward returns for holds 5..60
px_close = {c: price_dfs[c]['close'] for c in codes if c in price_dfs}
fwd = {h: {c: None for c in px_close} for h in HOLDS}
for c, s in px_close.items():
    ln = np.log(s.to_numpy())
    idx = s.index
    for h in HOLDS:
        r = pd.Series(np.nan, index=idx)
        if len(ln) > h:
            r.iloc[:-h] = ln[h:] - ln[:-h]
        fwd[h][c] = r
alpha_rows = []
for h in HOLDS:
    fr = pd.concat([fwd[h][c].rename('r').to_frame().assign(code=c) for c in px_close])
    fr = fr.dropna().reset_index()
    fr.columns = ['date', 'r', 'code']
    fr['date'] = pd.to_datetime(fr['date'])
    bench = fr.groupby('date')['r'].mean().rename('b')
    fr = fr.merge(bench, left_on='date', right_index=True)
    fr['alpha'] = fr['r'] - fr['b']
    ev = E0[E0['tier'] == 'ge3'][['code', 'date', 'year']].copy()
    ev = ev.merge(fr[['code', 'date', 'alpha', 'r']], on=['code', 'date'], how='left')
    for y in [2024, 2025, 2026]:
        ys = ev[ev['year'] == y]
        a = ys['alpha'].dropna()
        n = len(a)
        rec = {'hold': h, 'year': y, 'n': n, 'mean_alpha': round(float(a.mean()), 4) if n else np.nan,
               'median_alpha': round(float(a.median()), 4) if n else np.nan,
               'win_rate': round(float((a > 0).mean()), 3) if n else np.nan,
               'mean_ret': round(float(ys['r'].dropna().mean()), 4) if len(ys['r'].dropna()) else np.nan}
        if n >= 3 and a.std() > 0:
            t, p = stats.ttest_1samp(a, 0)
            rec['t'] = round(float(t), 2)
            rec['p'] = round(float(p), 4)
        alpha_rows.append(rec)
    # full-period
    a = ev['alpha'].dropna()
    rec = {'hold': h, 'year': 0, 'n': len(a), 'mean_alpha': round(float(a.mean()), 4),
           'median_alpha': round(float(a.median()), 4), 'win_rate': round(float((a > 0).mean()), 3),
           'mean_ret': round(float(ev['r'].dropna().mean()), 4)}
    if len(a) >= 3 and a.std() > 0:
        t, p = stats.ttest_1samp(a, 0)
        rec['t'] = round(float(t), 2)
        rec['p'] = round(float(p), 4)
    alpha_rows.append(rec)
adf = pd.DataFrame(alpha_rows)
adf.to_csv(f'{OUT}/bt019_event_alpha_by_year.csv', index=False)
print("\n=== EVENT-LEVEL alpha (ge3, td60 cluster, excess vs same-pool bench) ===")
print(adf.pivot_table(index='hold', columns='year', values='mean_alpha').round(4).to_string())

# =====================================================================
# 7. Rolling 6-month Sharpe on V5-20d NAV (ge3, gross + net)
# =====================================================================
evs3 = E0[E0['tier'] == 'ge3'].copy()
evs3['pos'] = 0.50
roll_rows = []
for cost, tag in [(0.0, 'gross'), (COST_SIDE, 'net')]:
    nav, st, tr = portfolio_sim(evs3, hold=20, cost_per_side=cost, entry_lag=0)
    rets = nav.pct_change().dropna()
    roll = rets.rolling(126).apply(lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan, raw=True)
    roll_s = roll.dropna()
    for lbl, v in [('min', roll_s.min()), ('median', roll_s.median()), ('max', roll_s.max()),
                   ('pct_gt0', (roll_s > 0).mean())]:
        roll_rows.append({'tag': tag, 'metric': lbl, 'value': round(float(v), 3)})
    # window breakdown
    roll_df = roll_s.to_frame('sharpe')
    roll_df['window'] = roll_df.index.year.astype(str) + '-H' + ((roll_df.index.month - 1) // 6 + 1).astype(str)
    for w, g in roll_df.groupby('window'):
        roll_rows.append({'tag': tag, 'metric': f'win_{w}', 'value': round(float(g['sharpe'].mean()), 3)})
roll = pd.DataFrame(roll_rows)
roll.to_csv(f'{OUT}/bt019_rolling_sharpe.csv', index=False)
print("\n=== ROLLING 6m Sharpe (V5 ge3 20d) ===")
print(roll.to_string(index=False))

# =====================================================================
# 8. Event density / concentration
# =====================================================================
e3_all = E0[E0['tier'] == 'ge3'].copy()
n_years_span = (SAMPLE_END - SAMPLE_START).days / 365.25
per_year = e3_all.groupby(e3_all['date'].dt.year).size()
conc = e3_all.groupby('code').size().sort_values(ascending=False)
den_rows = [{'metric': 'events_per_year_full', 'value': round(len(e3_all) / n_years_span, 1)},
            {'metric': 'events_2025', 'value': int(per_year.get(2025, 0))},
            {'metric': 'events_2026_to_aug13', 'value': int(per_year.get(2026, 0))},
            {'metric': 'events_2024h2', 'value': int(per_year.get(2024, 0))},
            {'metric': 'codes_with_events', 'value': int(e3_all['code'].nunique())},
            {'metric': 'events_per_code_mean', 'value': round(e3_all.groupby('code').size().mean(), 2)},
            {'metric': 'events_per_code_max', 'value': int(conc.max())},
            {'metric': 'top10_codes_share', 'value': round(float(conc.head(10).sum() / len(e3_all)), 3)},
            {'metric': 'top25_codes_share', 'value': round(float(conc.head(25).sum() / len(e3_all)), 3)},
            {'metric': 'single_code_max_share', 'value': round(float(conc.max() / len(e3_all)), 3)}]
den = pd.DataFrame(den_rows)
den.to_csv(f'{OUT}/bt019_event_density.csv', index=False)
print("\n=== EVENT DENSITY (ge3, td60) ===")
print(den.to_string(index=False))

# =====================================================================
# 9. Benchmarks: BH pool avg, BH 510300, random-entry control (5d & 20d)
# =====================================================================
bench_rows = []
# buy-and-hold pool average (equal weight, no rebalance)
bh_rets = []
for c in codes:
    if c not in px_close:
        continue
    s = px_close[c]
    s_act = s[s.index >= SAMPLE_START]
    if len(s_act) < 30:
        continue
    bh_rets.append(float(s_act.iloc[-1] / s_act.iloc[0] - 1))
bench_rows.append({'bench': 'pool_avg_bh', 'total_ret': round(float(np.mean(bh_rets)), 4),
                   'n': len(bh_rets), 'ann_sharpe': np.nan})
# 510300 BH
for g in glob.glob(f'{DAILY}/510300*.csv'):
    if '.bak' in g:
        continue
    r = pd.read_csv(g)
    r['date'] = pd.to_datetime(r['date'])
    r = r.set_index('date')['close'].sort_index()
    r_act = r[r.index >= SAMPLE_START]
    bh_300 = float(r_act.iloc[-1] / r_act.iloc[0] - 1)
    rets = r_act.pct_change().dropna()
    bench_rows.append({'bench': 'csi300_etf_bh', 'total_ret': round(bh_300, 4),
                       'n': len(r_act), 'ann_sharpe': round(float(rets.mean() / rets.std() * np.sqrt(252)), 3)})
    break

# random-entry control: same event count per code, uniform random dates, same holds
rng = np.random.default_rng(7)
n_events_by_code = e3_all.groupby('code').size().to_dict()
valid_dates_by_code = {}
for c, cnt in n_events_by_code.items():
    if c in px_close:
        v = px_close[c].index[px_close[c].index >= SAMPLE_START]
        if len(v) > cnt:
            valid_dates_by_code[c] = v
rand_rows = []
for h in [5, 20]:
    sh_dist, tot_dist = [], []
    for ri in range(300):
        rand_ev = []
        for c, v in valid_dates_by_code.items():
            cnt = n_events_by_code[c]
            pick = pd.DatetimeIndex(rng.choice(v, cnt, replace=True))
            for d in pick:
                rand_ev.append({'code': c, 'date': d, 'pos': 0.5})
        rd = pd.DataFrame(rand_ev)
        nav, st, tr = portfolio_sim(rd, hold=h, cost_per_side=0.0, entry_lag=0)
        if st.get('n_trades', 0) and len(nav) > 30:
            sh_dist.append(st['ann_sharpe'])
            tot_dist.append(st['total_ret'])
    sh_dist = np.array(sh_dist)
    tot_dist = np.array(tot_dist)
    rand_rows.append({'hold': h, 'n_reps': len(sh_dist),
                      'random_sharpe_mean': round(float(sh_dist.mean()), 3),
                      'random_sharpe_p5': round(float(np.percentile(sh_dist, 5)), 3),
                      'random_sharpe_median': round(float(np.percentile(sh_dist, 50)), 3),
                      'random_sharpe_p95': round(float(np.percentile(sh_dist, 95)), 3),
                      'random_total_ret_mean': round(float(tot_dist.mean()), 3),
                      'random_total_ret_p5': round(float(np.percentile(tot_dist, 5)), 3),
                      'random_total_ret_p95': round(float(np.percentile(tot_dist, 95)), 3)})
    # V5 comparison
    evs = evs3 if h == 20 else E0[E0['tier'] == 'ge3'].assign(pos=0.5)
    nav, st, tr = portfolio_sim(evs, hold=h, cost_per_side=0.0, entry_lag=0)
    pct_rank = float((sh_dist < st['ann_sharpe']).mean())
    rand_rows[-1]['v5_sharpe'] = round(st['ann_sharpe'], 3)
    rand_rows[-1]['v5_pctile_of_random'] = round(pct_rank, 3)
    rand_rows[-1]['v5_total_ret'] = round(st['total_ret'], 3)

# supplementary random controls: net-cost 20d (ge3 count), 30d (ge3 count), 20d ge4 count
def random_distribution(hold, n_reps, cost_per_side, count_by_code, seed_off=0):
    r2 = np.random.default_rng(100 + seed_off)
    sh, tot = [], []
    for _ in range(n_reps):
        rand_ev = []
        for c, v in valid_dates_by_code.items():
            cnt = count_by_code.get(c, 0)
            if cnt <= 0:
                continue
            pick = pd.DatetimeIndex(r2.choice(v, cnt, replace=True))
            for d in pick:
                rand_ev.append({'code': c, 'date': d, 'pos': 0.5})
        rd = pd.DataFrame(rand_ev)
        nav, st, tr = portfolio_sim(rd, hold=hold, cost_per_side=cost_per_side, entry_lag=0)
        if st.get('n_trades', 0) and len(nav) > 30:
            sh.append(st['ann_sharpe'])
            tot.append(st['total_ret'])
    return np.array(sh), np.array(tot)

n_ev_ge4 = E0[E0['tier'] == 'ge4'].groupby('code').size().to_dict()
for hold, cost, cbc, nreps, lbl in [(20, COST_SIDE, n_events_by_code, 150, '20d_net_ge3'),
                                    (30, 0.0, n_events_by_code, 150, '30d_gross_ge3'),
                                    (20, 0.0, n_ev_ge4, 150, '20d_gross_ge4')]:
    sh, tot = random_distribution(hold, nreps, cost, cbc, seed_off=len(rand_rows) * 7)
    if len(sh):
        rand_rows.append({'hold': hold, 'n_reps': len(sh), 'label': lbl,
                          'random_sharpe_mean': round(float(sh.mean()), 3),
                          'random_sharpe_p5': round(float(np.percentile(sh, 5)), 3),
                          'random_sharpe_median': round(float(np.percentile(sh, 50)), 3),
                          'random_sharpe_p95': round(float(np.percentile(sh, 95)), 3),
                          'random_total_ret_mean': round(float(tot.mean()), 3)})
        evs_l = evs3 if 'ge3' in lbl else E0[E0['tier'] == 'ge4'].assign(pos=0.5)
        nav, st, tr = portfolio_sim(evs_l, hold=int(lbl.split('d_')[0]), cost_per_side=cost, entry_lag=0)
        rand_rows[-1]['v5_sharpe'] = round(st['ann_sharpe'], 3)
        rand_rows[-1]['v5_pctile_of_random'] = round(float((sh < st['ann_sharpe']).mean()), 3)
        rand_rows[-1]['v5_total_ret'] = round(st['total_ret'], 3)
rand = pd.DataFrame(rand_rows)
rand.to_csv(f'{OUT}/bt019_random_entry_control.csv', index=False)
print("\n=== BENCHMARKS ===")
print(pd.DataFrame(bench_rows).to_string(index=False))
print("\n=== RANDOM-ENTRY CONTROL (300 reps, gross) ===")
print(rand.to_string(index=False))

# =====================================================================
# 10. Cost sweep — breakeven per-side cost (ge3, holds 5/10/20/30)
# =====================================================================
sweep_rows = []
for h in [5, 10, 20, 30]:
    nav0, st0, _ = portfolio_sim(evs3, hold=h, cost_per_side=0.0, entry_lag=0)
    sharpe0, tot0 = st0['ann_sharpe'], st0['total_ret']
    for c in [0.0005, 0.001, 0.0015, 0.002, 0.00275, 0.004, 0.006, 0.008, 0.01, 0.015, 0.02, 0.03]:
        nav, st, _ = portfolio_sim(evs3, hold=h, cost_per_side=c, entry_lag=0)
        sweep_rows.append({'hold': h, 'cost_per_side': c, 'ann_sharpe': st['ann_sharpe'],
                           'total_ret': st['total_ret']})
    sweep_rows.append({'hold': h, 'cost_per_side': 0.0, 'ann_sharpe': sharpe0, 'total_ret': tot0})
sweep = pd.DataFrame(sweep_rows)
sweep.to_csv(f'{OUT}/bt019_cost_sweep.csv', index=False)
# breakeven interpolation
be_rows = []
for h in [5, 10, 20, 30]:
    s = sweep[sweep['hold'] == h].sort_values('cost_per_side')
    for col in ['ann_sharpe', 'total_ret']:
        v = s[col].to_numpy()
        c = s['cost_per_side'].to_numpy()
        # find crossing of 0
        for i in range(len(v) - 1):
            if v[i] >= 0 >= v[i + 1]:
                frac = v[i] / (v[i] - v[i + 1]) if (v[i] - v[i + 1]) != 0 else 0
                be_rows.append({'hold': h, 'metric': col, 'breakeven_cost_per_side': round(float(c[i] + frac * (c[i + 1] - c[i])), 4)})
                break
bedf = pd.DataFrame(be_rows)
bedf.to_csv(f'{OUT}/bt019_breakeven_cost.csv', index=False)
print("\n=== BREAKEVEN per-side cost (ge3; 0.275%/side = 0.00275) ===")
print(bedf.to_string(index=False))

# =====================================================================
# 11. Monthly returns (V5 ge3 20d, gross + net)
# =====================================================================
for cost, tag in [(0.0, 'gross'), (COST_SIDE, 'net')]:
    nav, st, tr = portfolio_sim(evs3, hold=20, cost_per_side=cost, entry_lag=0)
    m = nav.resample('ME').last().pct_change().dropna().mul(100)
    m.to_frame('monthly_ret_pct').to_csv(f'{OUT}/bt019_monthly_{tag}.csv')
    print(f"\n=== MONTHLY returns ({tag}, %) ===")
    print(m.round(2).to_string())

# =====================================================================
# 12. Sensitivity: cluster gap 20/90 trading days (ge3, 20d hold, gross+net);
#     limit-up entry fraction
# =====================================================================
sens_rows = []
for gap in [20, 60, 90]:
    ev_rows = []
    for c in codes:
        sub = df[df['code'] == c].sort_values('date').set_index('date')
        if c not in price_dfs:
            continue
        ci = price_dfs[c].index
        ev = cluster_td(sub[sub['score'] >= 3], ci, min_gap=gap)
        for i in range(len(ev)):
            row = ev.iloc[i]
            ev_rows.append({'code': c, 'date': ev.index[i], 'score': int(row['score'])})
    ev = pd.DataFrame(ev_rows)
    ev['date'] = pd.to_datetime(ev['date'])
    ev['pos'] = 0.5
    for cost, tag in [(0.0, 'gross'), (COST_SIDE, 'net')]:
        nav, st, tr = portfolio_sim(ev, hold=20, cost_per_side=cost, entry_lag=0)
        sens_rows.append({'cluster_gap': gap, 'tag': tag, 'n_events': len(ev), **st})
sens = pd.DataFrame(sens_rows)
sens.to_csv(f'{OUT}/bt019_cluster_sensitivity.csv', index=False)
print("\n=== CLUSTER GAP SENSITIVITY (ge3, 20d hold) ===")
print(sens.to_string(index=False))

# limit-up entry fraction (can you actually buy at entry close?)
lu_rows = []
for c, s in px_close.items():
    evs_c = evs3[evs3['code'] == c]
    if not len(evs_c):
        continue
    ret = s.pct_change()
    for _, e in evs_c.iterrows():
        d = e['date']
        if d in ret.index:
            rr = float(ret.loc[d])
            main_lim = rr >= 0.095
            gz_lim = (c.startswith(('300', '688'))) and rr >= 0.195
            lu_rows.append({'code': c, 'date': d, 'entry_ret': rr, 'limit_up': bool(main_lim or gz_lim)})
ludf = pd.DataFrame(lu_rows)
lu_frac = float(ludf['limit_up'].mean()) if len(ludf) else 0.0
print(f"\nlimit-up entries fraction (ge3 td60): {lu_frac:.1%} of {len(ludf)}")
json.dump({'limit_up_entry_fraction': round(lu_frac, 4), 'n_entries': int(len(ludf))},
          open(f'{OUT}/bt019_limit_up.json', 'w'))

# =====================================================================
# 13. Summary JSON
# =====================================================================
grid20 = grid[(grid['hold'] == 20) & (grid['tier'] == 'ge3')]
g = grid20[grid20['tag'] == 'gross']
n = grid20[grid20['tag'] == 'net']
t1 = grid20[grid20['tag'] == 'net_t1']
res = {
    'question': 'Is V5 (ge3 observation-zone, uniform 50%, short-hold) a robust edge or a 2026 sample artifact?',
    'sample': f'{SAMPLE_START.date()}..{SAMPLE_END.date()}',
    'events_td60': {'ge3': int(len(E0[E0['tier']=='ge3'])), 'ge4': int(len(E0[E0['tier']=='ge4']))},
    'v5_20d': {
        'gross_sharpe': float(g['ann_sharpe'].iloc[0]) if len(g) else None,
        'gross_total': float(g['total_ret'].iloc[0]) if len(g) else None,
        'net_sharpe': float(n['ann_sharpe'].iloc[0]) if len(n) else None,
        'net_total': float(n['total_ret'].iloc[0]) if len(n) else None,
        'net_t1_sharpe': float(t1['ann_sharpe'].iloc[0]) if len(t1) else None,
        'net_t1_total': float(t1['total_ret'].iloc[0]) if len(t1) else None,
    },
    'bt017_repro': rep.to_dict('records'),
    'random_control': rand.to_dict('records'),
    'breakeven': bedf.to_dict('records'),
    'limit_up_entry_fraction': round(lu_frac, 4),
    'notes': [
        'BT-017 reported V5-20d Sharpe 0.839 used (a) event-index clustering (gap>=60 events, not trading days)',
        'and (b) full-calendar NAV anchored 2022-11 (~450 flat pre-sample days) -> Sharpe inflated.',
        'BT-019 fixes both; comparisons vs BT-017 must account for this.',
    ],
}
with open(f'{OUT}/summary.json', 'w') as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)

E0.to_csv(f'{OUT}/bt019_events_ge3_ge4_td60.csv', index=False)
print("\nDone. outputs ->", OUT)
