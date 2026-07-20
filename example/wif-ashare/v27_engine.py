#!/usr/bin/env python3
"""
WIF v2.7 独立回测引擎
======================
基于 wif_framework.ashare 包。
通过 WIF_ASHARE_DATA_DIR 环境变量可指定数据目录。

用法:
    python3 example/wif-ashare/v27_engine.py
    WIF_ASHARE_DATA_DIR=/path/to/data python3 example/wif-ashare/v27_engine.py
"""
import os, sys, json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".opencode", "python", "wif-framework"))

from wif_framework.ashare import (
    run_backtest,
    load_data,
    COST,
    TREND_UP,
    TREND_DOWN,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

if __name__ == "__main__":
    print("=" * 80)
    print("WIF v2.7 回测引擎（A股）")
    print("v2.5 + Direction A（MA60趋势覆盖）")
    print("=" * 80)

    os.environ.setdefault("WIF_ASHARE_DATA_DIR", str(os.path.abspath(DATA_DIR)))

    result = run_backtest()
    s = result["stats"]
    d = result["diagnostics"]

    print(f"\n[v2.7] NAV={s['nav_end']}  累计+{s['cumulative']}%  "
          f"年化+{s['geo_cagr']}%  夏普={s['sharpe']}  "
          f"MDD={s['mdd']}%  波动={s['volatility']}%")
    print(f"       再平衡: {result['rebal_count']}次  "
          f"总换手率: {result['total_turnover']:.4f}")

    print(f"\nDirection A 诊断:")
    print(f"  MA60上穿(+7%)天数: {d['trend_up_days']}天")
    print(f"  MA60下穿(-7%)天数: {d['trend_dn_days']}天")
    print(f"  其中MCI被覆盖升级Q1天数: {d['override_q1_days']}天")
    print(f"  其中MCI被覆盖降级Q3天数: {d['override_q3_days']}天")

    # 年度分析
    etf = load_data()
    etf_s = etf.iloc[1:].reset_index(drop=True).copy()
    etf_s["NAV_v27"] = result["nav_series"]
    etf_s["Eff_Q"] = result["eff_qs"]

    print(f"\n{'年份':<6} {'v2.7':>10} {'沪深300':>10} {'Δv27vsHS':>12}")
    print("-" * 50)
    for yr in sorted(etf_s["Year"].unique()):
        g = etf_s[etf_s["Year"] == yr]
        if len(g) < 20:
            continue
        r_v27 = g["NAV_v27"].iloc[-1] / g["NAV_v27"].iloc[0] - 1
        yr_idx = etf["Year"] == yr
        rhs = etf.loc[yr_idx, "hs300"].iloc[-1] / etf.loc[yr_idx, "hs300"].iloc[0] - 1 if yr_idx.sum() >= 20 else 0
        print(f"  {yr:<4} {r_v27 * 100:>+10.1f}% {rhs * 100:>+10.1f}% {(r_v27 - rhs) * 100:>+12.1f}pp")

    # 保存结果
    out = etf[["Date", "Year", "Q", "MCI", "trend"]].iloc[1:].reset_index(drop=True).copy()
    out["NAV_v27"] = result["nav_series"]
    out["Eff_Q"] = result["eff_qs"]
    out["EM"] = result["em_lvs"]
    out.to_csv(os.path.join(DATA_DIR, "nav_v27.csv"), index=False)
    print(f"\nNAV已保存: data/nav_v27.csv ({len(out)}行)")

    final = {
        "version": "v2.7",
        "engine": "ashare.py",
        "stats": s,
        "diagnostics": d,
        "rebal_count": result["rebal_count"],
        "total_turnover": result["total_turnover"],
    }
    with open(os.path.join(DATA_DIR, "v27_stats.json"), "w") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
    print(f"统计已保存: data/v27_stats.json")
    print("\n完成.")
