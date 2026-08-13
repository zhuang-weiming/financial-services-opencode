"""BT-012 跨年验证: SELL_LADDER v2.5 分级计票规则在 2025 全年的适用性
复用 BT-011 的 signal_cache_v2.parquet（覆盖 2024-10 ~ 2026-08）与 pool_200,
窗口改为 2025-01-02 → 2025-12-31（非弱市对照年, 与 BT-011 2026 弱市形成对比）。
指标: excess / win_rate / DD / 年化 Sharpe / 阶段分布 + V4 vs V0 配对检验。
"""
import sys, json, os
import numpy as np
import pandas as pd
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'BT-011'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'sell-ladder'))
import sell_ladder as sl
from data_loader import load_daily

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, 'results')
BT11 = os.path.join(os.path.dirname(BASE), 'BT-011')
POOL_FILE = os.path.join(BT11, 'pool_200.json')
CACHE_FILE = os.path.join(BT11, 'results', 'signal_cache_v2.parquet')
START, END = '2025-01-02', '2025-12-31'

EVENT_SIGNALS = sl.EVENT_SIGNALS
TREND_SIGNALS = sl.TREND_SIGNALS

def variant_fns():
    def v_v25(w_event=2, w_trend=1, penalize_trend=False):
        def f(ev_p, ev_n, tr_p, tr_n):
            s = w_event*ev_p + w_trend*tr_p - w_event*ev_n
            if penalize_trend: s -= w_trend*tr_n
            return s
        return f
    return {
        'V0_v25':    v_v25(2, 1, False),
        'V1_equal':  v_v25(1, 1, False),
        'V2_penN':   v_v25(2, 1, True),
        'V3_eqPenN': v_v25(1, 1, True),
        'V4_event':  v_v25(2, 0, False),
    }

def run():
    sig_cache = {}
    for code, g in pd.read_parquet(CACHE_FILE).groupby('code'):
        sig_cache[code] = g.reset_index(drop=True)
    pool = json.load(open(POOL_FILE))
    variants = variant_fns()
    stage_rule = {1:1.0, 2:0.7, 2.5:0.8, 3:0.2}

    df_cache = {}
    for p in pool:
        try:
            df_cache[p['code']] = load_daily(p['code']).reset_index(drop=True)
        except Exception:
            pass

    THR = [('v25_orig', 9.1, 5.88), ('thr_hi', 5.0, 3.0),
           ('thr_mid', 3.0, 2.0), ('thr_lo', 2.0, 1.0)]

    rows, per_stock = [], {}
    for tname, thr1, thr2 in THR:
        for vname, vfn in variants.items():
            stats_list, sharps, bh_sharps = [], [], []
            for p in pool:
                code = p['code']
                if code not in sig_cache or code not in df_cache: continue
                df, sig = df_cache[code], sig_cache[code]
                d = df['date'].dt.strftime('%Y-%m-%d').values
                close = df['close'].values
                idx = np.where((d >= START) & (d <= END))[0]
                if len(idx) < 100: continue
                lookup = {sd: sig.iloc[j] for j, sd in enumerate(sig['date'].values)}
                pos_series, stage_cnt = [], {}
                for t in idx:
                    row = lookup.get(d[t])
                    if row is None:
                        pos_series.append(1.0); continue
                    ev_p = ev_n = tr_p = tr_n = 0
                    for k in EVENT_SIGNALS:
                        v = row[k]
                        if v > 0: ev_p += 1
                        elif v < 0: ev_n += 1
                    for k in TREND_SIGNALS:
                        v = row[k]
                        if v > 0: tr_p += 1
                        elif v < 0: tr_n += 1
                    s = vfn(ev_p, ev_n, tr_p, tr_n)
                    ec = int(row['end_count'])
                    if s >= thr1 and ec <= 1: st = 1
                    elif s >= thr2 and ec <= 2: st = 2
                    elif s < thr2 and ec >= 3: st = 3
                    elif s < thr2 and ec < 3: st = 2.5
                    else: st = 2
                    stage_cnt[st] = stage_cnt.get(st, 0) + 1
                    pos_series.append(stage_rule.get(st, 1.0))
                pos = np.array(pos_series)
                eff = np.concatenate([[1.0], pos[:-1]])
                rets = np.diff(close[idx]) / close[idx[:-1]] * eff[1:]
                bh = np.diff(close[idx]) / close[idx[:-1]]
                nav = np.cumprod(1+rets); bhn = np.cumprod(1+bh)
                dd = float((nav/np.maximum.accumulate(nav)-1).min())
                def sharpe(r):
                    if len(r) < 30 or np.std(r) == 0: return np.nan
                    return float(np.mean(r)/np.std(r)*np.sqrt(252))
                sharps.append(sharpe(rets)); bh_sharps.append(sharpe(bh))
                stage_idx = [i for i in range(1, len(idx)) if pos[i-1] < 1.0]
                corr = tot = 0
                for i in stage_idx:
                    if i+5 < len(idx):
                        tot += 1
                        if close[idx[i+5]]/close[idx[i]]-1 < 0: corr += 1
                acc = corr/tot if tot else np.nan
                stats_list.append({'code': code,
                    'excess': float(nav[-1]/bhn[-1]-1), 'dd': dd, 'acc': acc,
                    'st1': stage_cnt.get(1,0)/len(idx), 'st2': stage_cnt.get(2,0)/len(idx),
                    'st25': stage_cnt.get(2.5,0)/len(idx), 'st3': stage_cnt.get(3,0)/len(idx)})
            sdf = pd.DataFrame(stats_list)
            s = np.array(sharps)
            rows.append({'thr': tname, 'variant': vname, 'n': len(sdf),
                'excess_pct': float(sdf['excess'].mean()*100),
                'win_rate': float((sdf['excess']>0).mean()*100),
                'dd_pct': float(sdf['dd'].mean()*100),
                'sharpe_mean': float(np.nanmean(s)), 'sharpe_med': float(np.nanmedian(s)),
                'bh_sharpe_mean': float(np.nanmean(bh_sharps)),
                'sharpe_gt_bh_pct': float(100*np.nanmean(np.array(sharps) > np.array(bh_sharps))),
                'trim_acc': float(sdf['acc'].mean()*100),
                'st1_pct': float(sdf['st1'].mean()*100), 'st2_pct': float(sdf['st2'].mean()*100),
                'st25_pct': float(sdf['st25'].mean()*100), 'st3_pct': float(sdf['st3'].mean()*100)})
            per_stock[(tname, vname)] = (sdf, np.array(sharps))

    res = pd.DataFrame(rows)
    out = os.path.join(OUT_DIR, 'bt012_scan_2025.csv')
    res.to_csv(out, index=False)

    print('='*100)
    print('BT-012 跨年验证: 2025-01-02 → 2025-12-31 (200 池; BH Sharpe 均值见 bh_sharpe_mean)')
    print('='*100)
    for tname, _, _ in THR:
        sub = res[res['thr']==tname]
        print(f"\n[{tname}]")
        print(f"{'variant':10s} {'excess':>8s} {'win':>6s} {'DD':>7s} {'Sharpe':>7s} {'>BH':>5s} {'st1':>6s} {'st2':>6s} {'2.5':>6s} {'st3':>6s}")
        for _, r in sub.iterrows():
            print(f"{r['variant']:10s} {r['excess_pct']:7.2f}% {r['win_rate']:5.1f}% {r['dd_pct']:6.1f}% "
                  f"{r['sharpe_mean']:7.2f} {r['sharpe_gt_bh_pct']:4.0f}% {r['st1_pct']:5.1f}% {r['st2_pct']:5.1f}% "
                  f"{r['st25_pct']:5.1f}% {r['st3_pct']:5.1f}%")

    print('\n' + '='*100)
    print('配对检验: V4_event vs V0_v25 (excess + Sharpe)')
    print('='*100)
    for tname, _, _ in THR:
        sdf4, sh4 = per_stock[(tname, 'V4_event')]
        sdf0, sh0 = per_stock[(tname, 'V0_v25')]
        m = sdf4.merge(sdf0, on='code', suffixes=('_4','_0'))
        d_ex = m['excess_4'] - m['excess_0']
        t_ex, p_ex = stats.ttest_rel(m['excess_4'], m['excess_0'])
        mask = ~(np.isnan(sh4) | np.isnan(sh0))
        t_sh, p_sh = stats.ttest_rel(sh4[mask], sh0[mask]) if mask.sum() > 10 else (np.nan, np.nan)
        print(f"{tname:9s}: V4 excess {d_ex.mean()*100:+.2f}pp (t={t_ex:.2f}, p={p_ex:.4f}, 胜出 {100*(d_ex>0).mean():.1f}%) "
              f"| Sharpe Δ {np.nanmean(sh4-sh0):+.3f} (t={t_sh:.2f}, p={p_sh:.4f})")

    print(f'\n→ {out}')

if __name__ == '__main__':
    run()