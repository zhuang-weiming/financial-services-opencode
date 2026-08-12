#!/usr/bin/env python3
"""精简大样本回测 v3.0 — 30 只股票 × 15 评估点 × 12 信号 (修复后版)

目标: < 5 分钟完成
输出: out/ladder_v3_signal_audit.json
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


def get_df(code):
    matches = list(Path(f"{ROOT}/data/market/daily").glob(f"{code}*.csv"))
    if not matches:
        return None
    try:
        return pd.read_csv(matches[0])
    except Exception:
        return None


def evaluate_one(code, n_eval=15, step=20):
    """单只股票: 12 信号在 n_eval 个评估点的 IC"""
    df = get_df(code)
    if df is None or len(df) < 400:
        return None

    c = df['close'].reset_index(drop=True) if 'date' in df.columns else df['close']
    peer_dfs = {p: get_df(p) for p in sp.get_peer_dfs(code, n_peers=8).keys()}
    peer_dfs = {k: v for k, v in peer_dfs.items() if v is not None and len(v) > 60}

    # 评估点: 取最近的 n_eval 个, 每 step 天取一个
    eval_idxs = list(range(len(df) - n_eval * step, len(df) - 20, step))[-n_eval:]

    sig_data = {name: {'signals': [], 'fwd': []} for name in SIGNAL_FUNCS}

    for idx in eval_idxs:
        sub = df.iloc[:idx+1].copy()
        if idx + 21 < len(c):
            fwd_ret = float(c.iloc[idx+21] / c.iloc[idx+1] - 1)
        else:
            fwd_ret = 0.0

        for sig_name, sig_func in SIGNAL_FUNCS.items():
            try:
                if sig_name == 'factor_research':
                    s = sig_func(sub, peer_dfs)
                else:
                    s = sig_func(sub)
                sig_data[sig_name]['signals'].append(s.get('signal', 0))
                sig_data[sig_name]['fwd'].append(fwd_ret)
            except Exception:
                sig_data[sig_name]['signals'].append(0)
                sig_data[sig_name]['fwd'].append(fwd_ret)

    # 计算每信号 IC
    result = {'code': code}
    for sig_name in SIGNAL_FUNCS:
        arr_s = np.array(sig_data[sig_name]['signals'])
        arr_f = np.array(sig_data[sig_name]['fwd'])
        triggered = (arr_s != 0).sum()
        trigger_rate = triggered / len(arr_s) if len(arr_s) else 0
        # IC: 用全部评估点的 Spearman (signal=0 算 0 票, 不是 NaN)
        # v3.0 修正: 原版只算 signal != 0 的子样本 → 当信号一直保持某方向时 IC=0
        if arr_s.std() > 0 and arr_f.std() > 0 and len(arr_s) >= 5:
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
            'triggered': int(triggered),
        }
    return result


def main():
    # 用户 18 只 + 12 只科技 + 20 只券商同行 = 50 只
    user_18 = ['601788', '600030', '601696', '601688', '601995', '601990',
               '601901', '512000', '600643', '600050', '601633', '601919',
               '002601', '300003', '300725', '600570', '300142', '601669']
    tech = ['688256', '688981', '688041', '002371', '300308', '300750',
            '603501', '002129', '002185', '300316', '300661', '600460']
    # 抽样补充
    all_files = list(Path(f"{ROOT}/data/market/daily").glob("*.csv"))
    all_codes = []
    import re
    for f in all_files:
        m = re.match(r"^(\d{6})", f.name)
        if m:
            all_codes.append(m.group(1))
    random.seed(42)
    extra = random.sample([c for c in all_codes if c not in user_18 + tech], 20)

    universe = list(dict.fromkeys(user_18 + tech + extra))
    print(f"测试 universe: {len(universe)} 只")

    results = []
    t0 = time.time()
    for i, code in enumerate(universe):
        if i % 10 == 0:
            print(f"  [{i}/{len(universe)}] {code}... elapsed {time.time()-t0:.0f}s")
        r = evaluate_one(code, n_eval=15, step=20)
        if r:
            results.append(r)
    print(f"\n完成 {len(results)} 只 (耗时 {time.time()-t0:.0f}s)")

    # 汇总
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
        }

    # 输出
    out_dir = Path(f"{ROOT}/out"); out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "ladder_v3_signal_audit.json"
    out_path.write_text(json.dumps({'summary': summary, 'n_results': len(results),
                                     'universe_size': len(universe),
                                     'eval_per_stock': 15},
                                    indent=2, ensure_ascii=False))

    print(f"\n=== 14 信号汇总 (n={len(results)} 只 A 股, {time.time()-t0:.0f}s) ===")
    print(f"{'信号':<22} {'meanIC':<9} {'stdIC':<8} {'触发率':<8} {'正IC%':<8}")
    print("-" * 60)
    for sig_name, s in sorted(summary.items(), key=lambda x: -abs(x[1]['mean_ic'])):
        print(f"{sig_name:<22} {s['mean_ic']:+.3f}    {s['std_ic']:.3f}    "
              f"{s['mean_trigger_rate']:.3f}    {s['positive_ic_pct']:.3f}")
    print(f"\n报告: {out_path}")


if __name__ == "__main__":
    main()