#!/usr/bin/env python3
"""100 只股票 × 16 信号 真日K日频评估 (1天1点)

用途: 与 5天1点(周K节奏)对比, 验证 smc/harmonic 等低频事件信号在日频评估下的真实触发率
"""
import sys
import json
import time
from pathlib import Path
from collections import defaultdict

import pandas as pd

ROOT = Path("/Users/weimingzhuang/Documents/source_code/financial-services-opencode")
sys.path.insert(0, str(ROOT / ".opencode/memory/personal-system/sell-ladder"))

import importlib.util
spec_sl = importlib.util.spec_from_file_location(
    "sl", str(ROOT / ".opencode/memory/personal-system/sell-ladder/sell_ladder.py"))
sl = importlib.util.module_from_spec(spec_sl); spec_sl.loader.exec_module(sl)

SIGNAL_FUNCS = {
    'alpha_engine_v21': sl.calc_alpha_engine_v21,
    'candlestick': sl.calc_candlestick,
    'ml_strategy': sl.calc_ml_strategy,
    'chanlun': sl.calc_chanlun,
    'technical_basic': sl.calc_technical_basic,
    'ichimoku': sl.calc_ichimoku,
    'smc': sl.calc_smc,
    'alpha_zoo': sl.calc_alpha_zoo,
    'factor_research': sl.calc_factor_research,
    'multi_factor': sl.calc_multi_factor,
    'volatility': sl.calc_volatility,
    'harmonic': sl.calc_harmonic,
    'pair_trading': sl.calc_pair_trading,
    'turnover_anomaly': sl.calc_turnover_anomaly,
    'sector_relative': sl.calc_sector_relative,
    'ad_line': sl.calc_ad_line,
}

# smc swing 敏感性
SMC_SWINGS = [10, 20]


def load_stock(code):
    """加载日K, 必须 pd.to_datetime 因为 chanlun 要 to_pydatetime"""
    matches = list((ROOT / "data/market/daily").glob(f"{code}*.csv"))
    if not matches:
        return None
    try:
        df = pd.read_csv(matches[0])
        df['date'] = pd.to_datetime(df['date'])
        if len(df) < 400:
            return None
        return df.reset_index(drop=True)
    except Exception:
        return None


def evaluate_stock(code, df, n_days=78, min_history=120):
    """1天1评估点 × n_days = 真实的日频评估 (最近 3 个月)"""
    c = df['close']
    # 每天 1 个评估点, 取最近 n_days 天
    start_idx = len(df) - n_days
    if start_idx < min_history:
        return None
    eval_idxs = list(range(start_idx, len(df), 1))  # 步长=1 = 每天

    sig_trigger = defaultdict(int)
    sig_total = defaultdict(int)
    sig_vals = defaultdict(list)
    ml_trigger = 0
    ml_total = 0
    ml_vals = []

    # ml_strategy 只跑最后 6 个点 (sklearn 慢)
    ml_points = set(eval_idxs[-6:])

    for idx in eval_idxs:
        sub = df.iloc[:idx + 1].copy()
        for sig_name, sig_func in SIGNAL_FUNCS.items():
            if sig_name == 'ml_strategy':
                if idx not in ml_points:
                    continue
                try:
                    s = sig_func(sub)
                    sig_val = s.get('signal', 0) if isinstance(s, dict) else 0
                except Exception:
                    sig_val = 0
                ml_total += 1
                if sig_val != 0:
                    ml_trigger += 1
                ml_vals.append(sig_val)
                continue
            try:
                if sig_name == 'factor_research':
                    s = sig_func(sub, {})
                elif sig_name == 'sector_relative':
                    s = sig_func(sub, sector_df=None, ticker=code)
                else:
                    s = sig_func(sub)
                sig_val = s.get('signal', 0) if isinstance(s, dict) else 0
            except Exception:
                sig_val = 0
            sig_total[sig_name] += 1
            if sig_val != 0:
                sig_trigger[sig_name] += 1
            sig_vals[sig_name].append(sig_val)

    sig_trigger['ml_strategy'] = ml_trigger
    sig_total['ml_strategy'] = ml_total
    sig_vals['ml_strategy'] = ml_vals

    smc_swing_results = {}
    for swing in SMC_SWINGS:
        trig = 0
        tot = 0
        for idx in eval_idxs:
            sub = df.iloc[:idx + 1].copy()
            try:
                s = sl.calc_smc(sub, swing_length=swing)
                sig_val = s.get('signal', 0) if isinstance(s, dict) else 0
            except Exception:
                sig_val = 0
            tot += 1
            if sig_val != 0:
                trig += 1
        smc_swing_results[f'swing_{swing}'] = {'trigger': trig, 'total': tot}

    return {
        'sig_trigger': dict(sig_trigger),
        'sig_total': dict(sig_total),
        'sig_vals': dict(sig_vals),
        'smc_swing': smc_swing_results,
    }


def main():
    pool = json.loads((ROOT / "out/pool_100_stocks.json").read_text())
    stocks = pool['wave'] + pool['holdings']
    print(f"测试股票池: {len(stocks)} 只 (82 波动样本 + 18 持仓)")
    print(f"评估: 1天1点 × 78 点 (≈3个月日K, 真实日频)")
    print(f"数据: data/market/daily/<code>*.csv (已是日K)")

    results = {}
    t0 = time.time()
    for i, code in enumerate(stocks, 1):
        df = load_stock(code)
        if df is None:
            print(f"  [{i}/{len(stocks)}] {code} 加载失败")
            continue
        res = evaluate_stock(code, df)
        if res is None:
            print(f"  [{i}/{len(stocks)}] {code} 数据不足")
            continue
        results[code] = res
        if i % 5 == 0 or i == len(stocks):
            elapsed = time.time() - t0
            avg = elapsed / i
            remain = (len(stocks) - i) * avg
            print(f"  [{i}/{len(stocks)}] 完成, 已用 {elapsed:.0f}s, 预计剩余 {remain:.0f}s")

    print(f"\n完成: {len(results)}/{len(stocks)} 只, 总耗时 {time.time()-t0:.0f}s")

    # 汇总
    print("\n" + "=" * 90)
    print("📊 100 只股票 × 16 信号 真日K日频触发率 (1天1点 × 78点)")
    print("=" * 90)
    print(f"{'信号':<22} {'平均触发率':<10} {'中位触发率':<10} {'正:%':<8} {'负:%':<8}")
    print("-" * 60)

    agg = {}
    for sig_name in SIGNAL_FUNCS:
        trigs, pos, neg = [], 0, 0
        for code, res in results.items():
            t = res['sig_trigger'].get(sig_name, 0)
            n = res['sig_total'].get(sig_name, 0)
            if n == 0:
                continue
            trigs.append(t / n)
            vals = res['sig_vals'].get(sig_name, [])
            pos += sum(1 for v in vals if v > 0)
            neg += sum(1 for v in vals if v < 0)
        if not trigs:
            continue
        avg = sum(trigs) / len(trigs)
        med = sorted(trigs)[len(trigs) // 2]
        total_vals = pos + neg
        pos_pct = pos / total_vals if total_vals else 0
        neg_pct = neg / total_vals if total_vals else 0
        agg[sig_name] = {
            'avg_trigger': round(avg, 4), 'median_trigger': round(med, 4),
            'pos': pos, 'neg': neg, 'pos_pct': round(pos_pct, 3),
        }
        print(f"{sig_name:<22} {avg:>7.1%}     {med:>8.1%}     {pos_pct:>6.1%}   {neg_pct:>6.1%}")

    # smc swing 敏感性
    print("\n" + "=" * 90)
    print("🔬 smc swing_length 敏感性 (1天1点)")
    print("=" * 90)
    swing_agg = {s: [] for s in SMC_SWINGS}
    for code, res in results.items():
        for k, v in res['smc_swing'].items():
            swing = int(k.split('_')[1])
            if v['total'] > 0:
                swing_agg[swing].append(v['trigger'] / v['total'])
    print(f"{'swing_length':<14} {'平均触发率':<10} {'中位触发率':<10} {'触发股票数':<10}")
    print("-" * 50)
    for swing in SMC_SWINGS:
        vals = swing_agg[swing]
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        med = sorted(vals)[len(vals) // 2]
        n_trigger = sum(1 for v in vals if v > 0)
        print(f"{swing:<14} {avg:>7.1%}     {med:>8.1%}     {n_trigger:>3}/{len(vals)}")

    out = {
        'method': 'dayK + 1d1eval × 78pts (≈3 months)',
        'results': results,
        'agg': agg,
        'smc_swing_agg': {str(k): v for k, v in swing_agg.items()},
    }
    (ROOT / "out/ladder_100stocks_daily_1d.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str))
    print(f"\n保存: out/ladder_100stocks_daily_1d.json")


if __name__ == "__main__":
    main()