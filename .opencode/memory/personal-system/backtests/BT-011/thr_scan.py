"""BT-011 阈值重校准扫描: 复用 signal_cache_v2.parquet, 遍历多组 (thr1, thr2) × 5 计票变体
验证假设: v2.5 固定比例阈值 (0.65/0.42·max) 在 2026 弱市信号分布下几乎不可达,
导致变体无区分度 → 用更低阈值恢复阶段 1/2 的出现, 让积分方式产生区分。
"""
import sys, json, os
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'sell-ladder'))
import sell_ladder as sl
from data_loader import load_daily

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, 'results')
POOL_FILE = os.path.join(BASE, 'pool_200.json')
CACHE_FILE = os.path.join(OUT_DIR, 'signal_cache_v2.parquet')
START, END, WARMUP = '2026-01-05', '2026-08-10', '2024-10-01'

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
        'V0_v25':     v_v25(2, 1, False),
        'V1_equal':   v_v25(1, 1, False),
        'V2_penN':    v_v25(2, 1, True),
        'V3_eqPenN':  v_v25(1, 1, True),
        'V4_event':   v_v25(2, 0, False),
    }

def run_thresholds(thr_sets):
    """thr_sets: list of (name, thr1, thr2)"""
    sig_cache = {}
    for code, g in pd.read_parquet(CACHE_FILE).groupby('code'):
        sig_cache[code] = g.reset_index(drop=True)
    pool = json.load(open(POOL_FILE))
    variants = variant_fns()
    stage_rule = {1:1.0, 2:0.7, 2.5:0.8, 3:0.2}

    # 预载所有 df (量小缓存 dict)
    df_cache = {}
    for p in pool:
        try:
            df_cache[p['code']] = load_daily(p['code']).reset_index(drop=True)
        except Exception:
            pass

    rows = []
    for tname, thr1, thr2 in thr_sets:
        for vname, vfn in variants.items():
            stats = []
            n_done = 0
            for p in pool:
                code = p['code']
                if code not in sig_cache or code not in df_cache:
                    continue
                df = df_cache[code]
                sig = sig_cache[code]
                # 只回放 2026
                d = df['date'].dt.strftime('%Y-%m-%d').values
                close = df['close'].values
                mask = (d >= START) & (d <= END)
                idx = np.where(mask)[0]
                if len(idx) < 20: continue
                sig_dates = sig['date'].values
                lookup = {}
                for j, sd in enumerate(sig_dates):
                    lookup[sd] = sig.iloc[j]
                pos_series = []
                stage_cnt = {}
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
                    st, _ = sl.stage_v22(s, 14, ec) if tname != 'v25_orig' else sl.stage_v22(s, 14, ec)
                    stage_cnt[st] = stage_cnt.get(st, 0) + 1
                    pos_series.append(stage_rule.get(st, 1.0))
                # 用自定义阈值判定 (覆盖 stage_v22 的固定比例阈值)
                pos_series2 = []
                stage_cnt2 = {}
                for t in idx:
                    row = lookup.get(d[t])
                    if row is None:
                        pos_series2.append(1.0); continue
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
                    stage_cnt2[st] = stage_cnt2.get(st, 0) + 1
                    pos_series2.append(stage_rule.get(st, 1.0))

                for plabel, pos, scnt in [('custom', pos_series2, stage_cnt2)]:
                    pos = np.array(pos)
                    eff = np.concatenate([[1.0], pos[:-1]])
                    rets = np.diff(close[idx]) / close[idx[:-1]] * eff[1:]
                    bh = np.diff(close[idx]) / close[idx[:-1]]
                    nav = np.cumprod(1+rets); bhn = np.cumprod(1+bh)
                    dd = float((nav/np.maximum.accumulate(nav)-1).min())
                    jul_m = (d[idx] >= '2026-07-01') & (d[idx] <= '2026-07-31')
                    jul_i = np.where(jul_m)[0]
                    jul_s = float(np.prod(1+rets[jul_i])-1) if len(jul_i)>1 else 0.0
                    jul_b = float(np.prod(1+bh[jul_i])-1) if len(jul_i)>1 else 0.0
                    stage_idx = [i for i in range(1,len(idx)) if pos[i-1] < 1.0]
                    corr = tot = 0
                    for i in stage_idx:
                        if i+5 < len(idx):
                            tot += 1
                            if close[idx[i+5]]/close[idx[i]]-1 < 0: corr += 1
                    acc = corr/tot if tot else np.nan
                    n_st1 = scnt.get(1,0)/len(idx)
                    n_st2 = scnt.get(2,0)/len(idx)
                    n_st25 = scnt.get(2.5,0)/len(idx)
                    n_st3 = scnt.get(3,0)/len(idx)
                    stats.append({'code': code,
                                  'excess': float(nav[-1]/bhn[-1]-1),
                                  'dd': dd, 'jul_s': jul_s, 'jul_b': jul_b,
                                  'acc': acc, 'st1': n_st1, 'st2': n_st2,
                                  'st25': n_st25, 'st3': n_st3})
                n_done += 1
            sdf = pd.DataFrame(stats)
            rows.append({
                'thr': f'{tname}', 'thr1': thr1, 'thr2': thr2, 'variant': vname, 'n': n_done,
                'excess_pct': float(sdf['excess'].mean()*100),
                'win_rate': float((sdf['excess']>0).mean()*100),
                'dd_pct': float(sdf['dd'].mean()*100),
                'jul_s_pct': float(sdf['jul_s'].mean()*100), 'jul_b_pct': float(sdf['jul_b'].mean()*100),
                'trim_acc': float(sdf['acc'].mean()*100),
                'st1_pct': float(sdf['st1'].mean()*100), 'st2_pct': float(sdf['st2'].mean()*100),
                'st25_pct': float(sdf['st25'].mean()*100), 'st3_pct': float(sdf['st3'].mean()*100),
            })
    res = pd.DataFrame(rows)
    out = os.path.join(OUT_DIR, 'thr_scan.csv')
    res.to_csv(out, index=False)
    print(res.to_string(index=False, float_format=lambda x: f'{x:7.2f}'))
    print(f'\n→ {out}')

if __name__ == '__main__':
    thr_sets = [
        ('v25_orig', 9.1, 5.88),
        ('thr_hi',   5.0, 3.0),
        ('thr_mid',  3.0, 2.0),
        ('thr_lo',   2.0, 1.0),
    ]
    run_thresholds(thr_sets)
