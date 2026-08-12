#!/usr/bin/env python3
"""大样本回测 v3.2 并行版 — 2966 只 × 52 周线评估点 × 14 信号 × 6 权重网格

v3.2 修正 (用户 8-11 反馈):
  - 旧版: 60 天 1 点 × 12 点 = 720 天 (过于稀疏 + 过长)
  - 新版: 5 天 1 点 × 52 点 = 260 天 ≈ 365 自然日 (周线评估节奏, 1 年中期视角)
  - 实盘盘后看周线信号, 1 周 1 次信号更新
  - 事件驱动信号 (smc/chanlun/ichimoku) 应在周线评估下表现更合理

v3.2 进一步 (用户 8-12 反馈):
  - multiprocessing 8 worker 并行 (2966 只独立计算, 完全不改变结果)
  - 不减少评估点 / 不减少股票数 / 不重新聚合旧 results
  - check_progress 每 200 只保存一次 (中断可恢复)
"""
import importlib.util
import json
import os
import re
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


def evaluate_one(code, n_eval=52, step=5):
    """v3.2 单只股票: 14 信号在 n_eval 个评估点的所有 signal 序列 + fwd20"""
    df = get_df(code)
    if df is None:
        return None

    c = df['close']
    peer_dfs = {p: get_df(p) for p in sp.get_peer_dfs(code, n_peers=8).keys()}
    peer_dfs = {k: v for k, v in peer_dfs.items() if v is not None and len(v) > 60}

    eval_idxs = list(range(max(252, len(df) - n_eval * step - 20),
                          len(df) - 20, step))[-n_eval:]
    if len(eval_idxs) < 12:
        return None

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
            'signals_seq': sig_data[sig_name]['signals'],
            'fwd20_seq': sig_data[sig_name]['fwd20'],
        }
    return result


def compute_score_for_grid(signals_dict, w_event, w_trend):
    """对一组 (signal, fwd20) 算 score 序列, 返回 (score_seq, fwd20_seq)"""
    sig_names = list(signals_dict.keys())
    first = signals_dict[sig_names[0]]
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


def _worker_one(code):
    """mp worker: 单只股票评估"""
    try:
        r = evaluate_one(code, n_eval=52, step=5)
        return ('ok', code, r)
    except Exception as e:
        return ('fail', code, str(e)[:100])


def main():
    global out_dir
    out_dir = Path(f"{ROOT}/out"); out_dir.mkdir(exist_ok=True)

    user_18 = ['601788', '600030', '601696', '601688', '601995', '601990',
               '601901', '512000', '600643', '600050', '601633', '601919',
               '002601', '300003', '300725', '600570', '300142', '601669']
    tech = ['688256', '688981', '688041', '002371', '300308', '300750',
            '603501', '002129', '002185', '300316', '300661', '600460']

    all_files = list(Path(f"{ROOT}/data/market/daily").glob("*.csv"))
    all_codes = []
    for f in all_files:
        m = re.match(r"^(\d{6})", f.name)
        if m:
            all_codes.append(m.group(1))
    universe = list(dict.fromkeys(user_18 + tech + all_codes))
    print(f"测试 universe: {len(universe)} 只 A 股 (用户18+科技12+数据池{len(all_codes)})")
    print(f"评估参数 (v3.2 周线): 5 天一个点 × 52 点 = 260 天窗口 ≈ 1 年中期视角")
    print(f"事件驱动信号 (smc/chanlun/ichimoku) 在周线评估下应表现更合理")
    print(f"并行 worker: 8 核 (10 核 CPU, 留 2 核系统)")

    # ====== resume 支持 ======
    raw_path = out_dir / "ladder_v3_2_weekly_results.json"
    progress_path = out_dir / "ladder_v3_2_weekly_progress.json"
    if raw_path.exists():
        try:
            done_data = json.loads(raw_path.read_text())
            done_codes = {r['code'] for r in done_data}
            results = done_data
            print(f"Resume: 已加载 {len(results)} 只 ({len(done_codes)} 个唯一代码)")
        except Exception:
            results = []
            done_codes = set()
    else:
        results = []
        done_codes = set()

    todo = [c for c in universe if c not in done_codes]
    print(f"待跑: {len(todo)} 只")

    if not todo:
        print("全部已完成, 跳到分析步骤")
    else:
        # ====== 并行执行 ======
        import multiprocessing as mp
        ctx = mp.get_context('fork')
        t0 = time.time()
        fail_count = 0
        last_save = time.time()
        BATCH_SAVE = 200  # 每 200 只保存一次

        with ctx.Pool(processes=8) as pool:
            for i, (status, code, payload) in enumerate(pool.imap_unordered(_worker_one, todo, chunksize=4)):
                if status == 'ok' and payload is not None:
                    results.append(payload)
                else:
                    fail_count += 1

                # 进度打印
                done_now = len(results)  # 全部已完成
                if (i + 1) % 50 == 0 or (i + 1) == len(todo):
                    elapsed = time.time() - t0
                    rate = (i + 1) / max(elapsed, 1)
                    eta = (len(todo) - i - 1) / max(rate, 0.1)
                    print(f"  [并行 {i+1}/{len(todo)} this batch | {done_now}/{len(universe)} total] "
                          f"fail={fail_count} elapsed={elapsed:.0f}s rate={rate:.2f}/s eta={eta:.0f}s",
                          flush=True)

                # 周期性保存
                if (i + 1) % BATCH_SAVE == 0 or time.time() - last_save > 300:
                    raw_path.write_text(json.dumps(results, ensure_ascii=False))
                    progress_path.write_text(json.dumps({
                        'last_done': code,
                        'total_done': len(results),
                        'total_todo': len(todo),
                        'elapsed': time.time() - t0,
                        'fail_count': fail_count,
                    }, ensure_ascii=False))
                    last_save = time.time()
                    print(f"  [checkpoint] saved {len(results)} results to {raw_path}")

        # 最终保存
        raw_path.write_text(json.dumps(results, ensure_ascii=False))
        elapsed = time.time() - t0
        print(f"\n完成: {len(results)} 只有效 (失败 {fail_count}, 总耗时 {elapsed:.0f}s)")

    # 汇总只用 ok 的 (filter None)
    results_ok = [r for r in results if r and 'alpha_engine_v21' in r]
    print(f"汇总分析: {len(results_ok)} 个有效结果")

    # ============ 信号 IC 汇总 ============
    summary = {}
    for sig_name in SIGNAL_FUNCS:
        if not results_ok:
            continue
        ics = [r[sig_name]['ic'] for r in results_ok]
        triggers = [r[sig_name]['trigger_rate'] for r in results_ok]
        summary[sig_name] = {
            'n_stocks': len(results_ok),
            'mean_ic': round(float(np.mean(ics)), 3),
            'std_ic': round(float(np.std(ics)), 3),
            'mean_trigger_rate': round(float(np.mean(triggers)), 3),
            'positive_ic_pct': round(sum(1 for x in ics if x > 0) / len(ics), 3) if ics else 0,
            'category': 'event' if sig_name in EVENT_SIGNALS else 'trend',
        }

    # ============ 权重网格搜索 ============
    weight_grid = {}
    grid_data = {f"e{w_e}_t{w_t}": {'scores': [], 'fwds': []} for w_e, w_t in WEIGHT_GRID}

    for r in results_ok:
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
    out_path = out_dir / "ladder_v3_2_weekly_audit.json"

    out_data = {
        'n_results': len(results_ok),
        'n_total_in_results': len(results),
        'universe_size': len(universe),
        'eval_per_stock': 52,
        'step_days': 5,
        'window_days': 260,
        'eval_mode': 'weekly',
        'n_workers': 8,
        'per_signal': summary,
        'weights_grid': weight_grid,
    }
    out_path.write_text(json.dumps(out_data, indent=2, ensure_ascii=False))
    print(f"\n报告: {out_path}")

    print(f"\n=== 14 信号汇总 (n={len(results_ok)} 只 A 股) ===")
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


if __name__ == "__main__":
    main()
