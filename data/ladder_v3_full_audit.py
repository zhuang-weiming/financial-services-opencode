#!/usr/bin/env python3
"""大样本回测 v3.1 — 2966 只 A 股 × 长窗口 60 天 × 14 信号 × 6 权重组合

输出: out/ladder_v3_full_audit.json
- per_signal: 每个信号的 IC + 触发率 (跨全 A 股)
- per_stock: 每只股票的 fwd20 序列 + score 序列 (用于权重网格)
- weights_grid: 6 个 (事件, 趋势) 权重组合下的 score → fwd20 IC
"""
import importlib.util
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = "/Users/weimingzhuang/Documents/source_code/financial-services-opencode"
sys.path.insert(0, f"{ROOT}/data")

# 加载模块
spec_sp = importlib.util.spec_from_file_location("sp", f"{ROOT}/data/sector_pool.py")
sp = importlib.util.module_from_spec(spec_sp); spec_sp.loader.exec_module(sp)

spec_sl = importlib.util.spec_from_file_location("sl", f"{ROOT}/.opencode/memory/personal-system/sell-ladder/sell_ladder.py")
sl = importlib.util.module_from_spec(spec_sl); spec_sl.loader.exec_module(sl)


SIGNAL_FUNCS = {
    'candlestick': sl.calc_candlestick,
    'chanlun': sl.calc_chanlun,
    'turnover_anomaly': sl.calc_turnover_anomaly,
    'alpha_engine_v21': sl.calc_alpha_engine_v21,
    'technical_basic': sl.calc_technical_basic,
    'ichimoku': sl.calc_ichimoku,
    'smc': sl.calc_smc,
    'alpha_zoo': sl.calc_alpha_zoo,
    'multi_factor': sl.calc_multi_factor,
    'ml_strategy': sl.calc_ml_strategy,
    'sector_relative': sl.calc_sector_relative,
    'volatility': sl.calc_volatility,
    'ad_line': sl.calc_ad_line,
    'factor_research': sl.calc_factor_research,
}

EVENT_SIGNALS = {'candlestick', 'chanlun', 'turnover_anomaly', 'multi_factor'}
TREND_SIGNALS = {'alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc',
                 'alpha_zoo', 'ml_strategy', 'sector_relative',
                 'volatility', 'ad_line', 'factor_research'}

WEIGHT_GRID = [(1, 1), (1.5, 1), (2, 1), (2.5, 1), (3, 1), (2, 1.5)]


def get_df(code):
    matches = list(Path(f"{ROOT}/data/market/daily").glob(f"{code}*.csv"))
    if not matches:
        return None
    try:
        df = pd.read_csv(matches[0])
        if len(df) < 400:
            return None
        return df
    except Exception:
        return None


def evaluate_one(code, n_eval=12, step=60):
    """单只股票: 14 信号在 n_eval 个评估点的所有 signal 序列 + fwd20"""
    df = get_df(code)
    if df is None:
        return None

    c = df['close']
    peer_dfs = {p: get_df(p) for p in sp.get_peer_dfs(code, n_peers=8).keys()}
    peer_dfs = {k: v for k, v in peer_dfs.items() if v is not None and len(v) > 60}

    eval_idxs = list(range(max(252, len(df) - n_eval * step - 20),
                          len(df) - 20, step))[-n_eval:]
    if len(eval_idxs) < 6:
        return None

    # sig_data[sig] = {'signals': [...], 'fwd20': [...], 'fwd60': [...]}
    sig_data = {name: {'signals': [], 'fwd20': [], 'fwd60': []} for name in SIGNAL_FUNCS}

    for idx in eval_idxs:
        sub = df.iloc[:idx+1].copy()
        if idx + 21 < len(c):
            fwd20 = float(c.iloc[idx+21] / c.iloc[idx+1] - 1)
        else:
            fwd20 = 0.0
        if idx + 61 < len(c):
            fwd60 = float(c.iloc[idx+61] / c.iloc[idx+1] - 1)
        else:
            fwd60 = 0.0

        for sig_name, sig_func in SIGNAL_FUNCS.items():
            try:
                if sig_name == 'factor_research':
                    s = sig_func(sub, peer_dfs)
                elif sig_name == 'sector_relative':
                    s = sig_func(sub, sector_df=None, ticker=code)
                else:
                    s = sig_func(sub)
                sig_val = s.get('signal', 0)
                sig_data[sig_name]['signals'].append(sig_val)
                sig_data[sig_name]['fwd20'].append(fwd20)
                sig_data[sig_name]['fwd60'].append(fwd60)
            except Exception:
                sig_data[sig_name]['signals'].append(0)
                sig_data[sig_name]['fwd20'].append(fwd20)
                sig_data[sig_name]['fwd60'].append(fwd60)

    # 计算每信号 IC (vs fwd20) — 用全部评估点
    result = {'code': code, 'len': len(df), 'n_eval': len(eval_idxs)}
    for sig_name in SIGNAL_FUNCS:
        arr_s = np.array(sig_data[sig_name]['signals'])
        arr_f = np.array(sig_data[sig_name]['fwd20'])
        triggered = int((arr_s != 0).sum())
        trigger_rate = triggered / len(arr_s) if len(arr_s) else 0
        if arr_s.std() > 0 and arr_f.std() > 0 and len(arr_s) >= 6:
            try:
                ic, _ = spearmanr(arr_s, arr_f)
                ic = float(ic) if not pd.isna(ic) else 0
            except Exception:
                ic = 0
        else:
            ic = 0
        result[sig_name] = {
            'ic': round(ic, 3),
            'trigger_rate': round(trigger_rate, 3),
            'triggered': triggered,
            'signals_seq': sig_data[sig_name]['signals'],  # 完整序列用于 grid
            'fwd20_seq': sig_data[sig_name]['fwd20'],
        }
    return result


def compute_score_for_grid(signals_dict, w_event, w_trend):
    """对一组 (signal, fwd20) 算 score 序列, 返回 (score_seq, fwd20_seq)
    signals_dict 的格式来自 evaluate_one: {sig_name: {'signals_seq': [...], 'fwd20_seq': [...]}}
    """
    sig_names = list(signals_dict.keys())
    first = signals_dict[sig_names[0]]
    # 兼容 'signals' 或 'signals_seq' 两种 key
    sig_key = 'signals_seq' if 'signals_seq' in first else 'signals'
    fwd_key = 'fwd20_seq' if 'fwd20_seq' in first else 'fwd20'
    n = len(first[sig_key])
    score_seq = np.zeros(n)
    fwd_seq = np.array(first[fwd_key])
    for sig_name, d in signals_dict.items():
        s = np.array(d[sig_key])
        w = w_event if sig_name in EVENT_SIGNALS else w_trend
        score_seq += s * w
    return score_seq, fwd_seq


def main():
    # 输出目录提前定义
    global out_dir
    out_dir = Path(f"{ROOT}/out"); out_dir.mkdir(exist_ok=True)

    # 全 universe
    user_18 = ['601788', '600030', '601696', '601688', '601995', '601990',
               '601901', '512000', '600643', '600050', '601633', '601919',
               '002601', '300003', '300725', '600570', '300142', '601669']
    tech = ['688256', '688981', '688041', '002371', '300308', '300750',
            '603501', '002129', '002185', '300316', '300661', '600460']

    all_files = list(Path(f"{ROOT}/data/market/daily").glob("*.csv"))
    all_codes = []
    import re
    for f in all_files:
        m = re.match(r"^(\d{6})", f.name)
        if m:
            all_codes.append(m.group(1))
    universe = list(dict.fromkeys(user_18 + tech + all_codes))
    print(f"测试 universe: {len(universe)} 只 A 股 (用户18+科技12+数据池{len(all_codes)})")
    print(f"评估参数: 60 天一个点 × 12 点 = 720 天窗口")

    results = []
    t0 = time.time()
    fail_count = 0
    for i, code in enumerate(universe):
        if i % 200 == 0:
            elapsed = time.time() - t0
            rate = i / max(elapsed, 1)
            eta = (len(universe) - i) / max(rate, 0.1)
            print(f"  [{i}/{len(universe)}] ok={len(results)} fail={fail_count} "
                  f"elapsed={elapsed:.0f}s rate={rate:.1f}/s eta={eta:.0f}s", flush=True)
        try:
            r = evaluate_one(code, n_eval=12, step=60)
            if r:
                results.append(r)
            else:
                fail_count += 1
        except Exception:
            fail_count += 1
    elapsed = time.time() - t0
    print(f"\n完成: {len(results)} 只有效 (失败 {fail_count}, 总耗时 {elapsed:.0f}s)")

    # 保存完整 results 到磁盘 (供权重网格等后续步骤使用, 避免再次丢失)
    raw_path = out_dir / "ladder_v3_full_results.json"
    raw_data = []
    for r in results:
        # 只保留 score 用到的字段 (signals_seq + fwd20_seq + code + len)
        slim = {'code': r['code'], 'len': r['len'], 'n_eval': r['n_eval']}
        for sig_name in SIGNAL_FUNCS:
            slim[sig_name] = {
                'signals_seq': r[sig_name]['signals_seq'],
                'fwd20_seq': r[sig_name]['fwd20_seq'],
            }
        raw_data.append(slim)
    raw_path.write_text(json.dumps(raw_data, ensure_ascii=False))
    print(f"原始 results 已保存: {raw_path} ({len(raw_data)} 只)")

    # ============ 信号 IC 汇总 ============
    summary = {}
    for sig_name in SIGNAL_FUNCS:
        ics = [r[sig_name]['ic'] for r in results]
        triggers = [r[sig_name]['trigger_rate'] for r in results]
        summary[sig_name] = {
            'n_stocks': len(results),
            'mean_ic': round(float(np.mean(ics)), 3),
            'std_ic': round(float(np.std(ics)), 3),
            'mean_trigger_rate': round(float(np.mean(triggers)), 3),
            'positive_ic_pct': round(sum(1 for x in ics if x > 0) / len(ics), 3) if ics else 0,
            'category': 'event' if sig_name in EVENT_SIGNALS else 'trend',
        }

    # ============ 权重网格搜索 (score vs fwd20 IC) ============
    weight_grid = {}
    all_scores, all_fwds = [], []  # 全局汇总

    # 聚合所有评估点的 score+fwd20
    grid_data = {f"e{w_e}_t{w_t}": {'scores': [], 'fwds': []} for w_e, w_t in WEIGHT_GRID}

    for r in results:
        for w_e, w_t in WEIGHT_GRID:
            sig_dict = {sn: r[sn] for sn in SIGNAL_FUNCS}
            score_seq, fwd_seq = compute_score_for_grid(sig_dict, w_e, w_t)
            key = f"e{w_e}_t{w_t}"
            grid_data[key]['scores'].extend(score_seq.tolist())
            grid_data[key]['fwds'].extend(fwd_seq.tolist())

    for key in grid_data:
        scores = np.array(grid_data[key]['scores'])
        fwds = np.array(grid_data[key]['fwds'])
        if len(scores) >= 100 and scores.std() > 0 and fwds.std() > 0:
            ic, _ = spearmanr(scores, fwds)
            ic = float(ic) if not pd.isna(ic) else 0
            mean_score = float(scores.mean())
            weight_grid[key] = {
                'ic_score_vs_fwd20': round(ic, 4),
                'n_obs': len(scores),
                'mean_score': round(mean_score, 3),
            }
        else:
            weight_grid[key] = {'ic_score_vs_fwd20': 0, 'n_obs': len(scores), 'mean_score': 0}

    # ============ 输出 ============
    out_path = out_dir / "ladder_v3_full_audit.json"

    # 简化: 不存完整序列 (太大), 只存汇总
    out_data = {
        'n_results': len(results),
        'n_failed': fail_count,
        'universe_size': len(universe),
        'eval_per_stock': 12,
        'step_days': 60,
        'window_days': 720,
        'elapsed_sec': round(elapsed, 1),
        'per_signal': summary,
        'weights_grid': weight_grid,
    }
    out_path.write_text(json.dumps(out_data, indent=2, ensure_ascii=False))

    print(f"\n=== 14 信号汇总 (n={len(results)} 只 A 股, {elapsed:.0f}s) ===")
    print(f"{'信号':<22} {'类别':<8} {'meanIC':<8} {'stdIC':<8} {'触发率':<8} {'正IC%':<8}")
    print("-" * 70)
    for sig_name, s in sorted(summary.items(), key=lambda x: -abs(x[1]['mean_ic'])):
        cat = '🟢事件' if s['category'] == 'event' else '🔵趋势'
        print(f"{sig_name:<22} {cat:<8} {s['mean_ic']:+.3f}   {s['std_ic']:.3f}    "
              f"{s['mean_trigger_rate']:.3f}    {s['positive_ic_pct']:.3f}")

    print(f"\n=== 权重网格 (score vs fwd20 IC) ===")
    print(f"{'事件×w':<10} {'趋势×w':<10} {'IC':<8} {'N':<8} {'meanScore':<10}")
    print("-" * 50)
    for w_e, w_t in WEIGHT_GRID:
        key = f"e{w_e}_t{w_t}"
        d = weight_grid[key]
        print(f"事件×{w_e:<5} 趋势×{w_t:<5}  {d['ic_score_vs_fwd20']:+.4f}  {d['n_obs']:<8} {d['mean_score']:<+.3f}")

    print(f"\n报告: {out_path}")


if __name__ == "__main__":
    main()