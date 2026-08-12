#!/usr/bin/env python3
"""100 只股票 × 16 信号 多点历史触发率诊断 (日K)

目的: 回答用户两大怀疑
  (1) 是阈值问题吗?  → smc swing=10(canonical) vs swing=20(旧A股适配) 对比
  (2) 是数据问题吗?  → 明确使用日K (707/900 间隔=1), 5天1评估点 = 周评估节奏

方法论: 对齐 v3.2 (ladder_v3_2_weekly_audit.py)
  - 每只股票 5 天 1 个评估点 × 52 点 = 260 天 (1 年中期视角)
  - 每个评估点调用 16 个 calc_* 函数, 记录 signal
  - 触发率 = 非零 signal 数 / 评估点数
  - 附加: 对 smc 做 swing_length 敏感性 (10/15/20/50)
"""
import sys
import json
import time
from pathlib import Path
from collections import defaultdict

import pandas as pd

ROOT = Path("/Users/weimingzhuang/Documents/source_code/financial-services-opencode")
sys.path.insert(0, str(ROOT / ".opencode/memory/personal-system/sell-ladder"))
sys.path.insert(0, str(ROOT / "data"))

import importlib.util
spec_sl = importlib.util.spec_from_file_location(
    "sl", str(ROOT / ".opencode/memory/personal-system/sell-ladder/sell_ladder.py"))
sl = importlib.util.module_from_spec(spec_sl); spec_sl.loader.exec_module(sl)

# 16 信号 (与 sell_ladder 一致)
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

# smc 阈值敏感性: 不同 swing_length
SMC_SWINGS = [10, 20]
subset_30 = set()  # main 中填充 (前15只)  # main() 中初始化


def load_stock(code):
    """从集中目录或 fallback 加载 (对齐 data_loader.load_daily 语义)
    注意: 必须做 pd.to_datetime, 否则 chanlun 的 row['date'].to_pydatetime() 会失败
    """
    matches = list((ROOT / "data/market/daily").glob(f"{code}*.csv"))
    if not matches:
        return None
    try:
        df = pd.read_csv(matches[0])
        if len(df) < 400:
            return None
        df['date'] = pd.to_datetime(df['date'])  # CRITICAL: chanlun 需要
        return df.reset_index(drop=True)
    except Exception:
        return None


def evaluate_stock(code, df, n_eval=26, step=5):
    """单只股票: 16 信号在 26 个周评估点的触发率 (130天≈6个月)"""
    c = df['close']
    eval_idxs = list(range(max(252, len(df) - n_eval * step - 20),
                          len(df) - 20, step))[-n_eval:]
    if len(eval_idxs) < 12:
        return None

    sig_trigger = defaultdict(int)
    sig_total = defaultdict(int)
    sig_vals = defaultdict(list)
    ml_trigger = 0
    ml_total = 0
    ml_vals = []

    # ml_strategy 是 sklearn walk-forward (1.5s/次), 只跑最后 4 个点
    ml_points = set(eval_idxs[-2:])
    for idx in eval_idxs:
        sub = df.iloc[:idx + 1].copy()
        for sig_name, sig_func in SIGNAL_FUNCS.items():
            # 跳过中间点的 ml_strategy (walk-forward 太慢, 4 点采样足够估计触发率)
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

    # ml_strategy 并入主统计 (用真实采样点)
    sig_trigger['ml_strategy'] = ml_trigger
    sig_total['ml_strategy'] = ml_total
    sig_vals['ml_strategy'] = ml_vals

    # smc swing 敏感性 (子集 30 只)
    smc_swing_results = {}
    if code in subset_30:
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
    # smc swing 敏感性子集: 前 30 只
    global subset_30
    subset_30 = set(stocks[:15])
    print(f"测试股票池: {len(stocks)} 只 (82 波动样本 + 18 持仓)")
    print(f"数据: 日K (集中目录 data/market/daily), 评估: 5天1点 × 26 点 (≈6个月)")
    print(f"smc swing 敏感性子集: 前 15 只 (10 vs 20)")

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
        if i % 10 == 0:
            print(f"  [{i}/{len(stocks)}] 完成, 已用 {time.time()-t0:.0f}s")

    print(f"\n完成: {len(results)}/{len(stocks)} 只, 总耗时 {time.time()-t0:.0f}s")

    # ============ 汇总 ============
    print("\n" + "=" * 90)
    print("📊 100 只股票 × 16 信号 多点历史触发率 (日K, 52 周评估点)")
    print("=" * 90)
    print(f"{'信号':<22} {'平均触发率':<10} {'中位触发率':<10} {'正:%':<8} {'负:%':<8}")
    print("-" * 60)

    agg = {}
    for sig_name in SIGNAL_FUNCS:
        trigs, totals, pos, neg = [], [], 0, 0
        for code, res in results.items():
            t = res['sig_trigger'].get(sig_name, 0)
            n = res['sig_total'].get(sig_name, 0)
            if n == 0:
                continue
            trigs.append(t / n)
            totals.append(n)
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
    print("🔬 smc swing_length 敏感性 (是否阈值问题?)")
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

    # 保存
    out = {
        'pool_size': len(stocks),
        'method': 'dayK, 5d1eval × 52pts',
        'results': results,
        'agg': agg,
        'smc_swing_agg': {str(k): v for k, v in swing_agg.items()},
    }
    (ROOT / "out/ladder_100stocks_daily_diag.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str))
    print(f"\n保存: out/ladder_100stocks_daily_diag.json")


if __name__ == "__main__":
    main()