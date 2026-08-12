#!/usr/bin/env python3
"""
BT-010 — BUY_LADDER v3.1 对比回测 (经典阈值 vs V21 OB filter)

对比 3 种买入信号配置 (月度调仓, 用 alpha-engine-v21 HDF5):
  C1 经典 LazyBear:  WT1 进入 [40, 60] sweet zone 且上一月 < 0 → 买入
  C2 V21 OB filter:  WT1 进入 [40, adaptive_ob] 且上一月 < 0 → 买入
                     其中 adaptive_ob = 53 + 40 × (1 - mcap_pctile)
  C3 基准:           买入持有 (BH) + 简单 MA60 突破

数据: data/data_v20.h5 (月度 prices + wt1_monthly + market_cap)

用法:
  python3 script.py [--n-hold 10] [--start 2012-01-31] [--out-dir .]

输出:
  results_by_variant.csv + summary.json
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL_ROOT = REPO_ROOT / ".opencode" / "skills" / "alpha-engine-v21"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from data_loader import load_v21_data

DEFAULT_H5 = REPO_ROOT / ".opencode" / "skills" / "alpha-engine-v21" / "data" / "data_v20.h5"


def compute_adaptive_ob(mcap_row: pd.Series, ob_base=53, ob_cap_adj=40) -> pd.Series:
    """V21 adaptive OB threshold: ob_base + ob_cap_adj * (1 - mcap_pctile)
    mcap_pctile = 0 → threshold = 53 + 40 = 93 (大盘, 高阈值)
    mcap_pctile = 1 → threshold = 53 (小盘, 低阈值)
    """
    mcap_pct = 1 - mcap_row.rank(pct=True)  # 大盘 → 小 pct
    return ob_base + ob_cap_adj * mcap_pct


def detect_c1_signals(wt1_df, hold_months=1):
    """C1: 经典 [40, 60] sweet zone, 上一月 < 0"""
    cur = wt1_df
    prev = wt1_df.shift(1)
    in_zone = (cur >= 40) & (cur <= 60)
    came_from_below = prev < 0
    signals = in_zone & came_from_below
    return signals


def detect_c2_signals(wt1_df, mcap_df):
    """C2: V21 adaptive OB sweet zone [40, adaptive_ob], 上一月 < 0
    对齐 wt1 与 mcap 的日期索引 (wt1 1990-2026, mcap 2010-2026)"""
    wt1_aligned = wt1_df.reindex(mcap_df.index)
    prev = wt1_aligned.shift(1)
    came_from_below = prev < 0
    adaptive_ob = pd.DataFrame(
        {dt: compute_adaptive_ob(mcap_df.loc[dt]) for dt in mcap_df.index}
    ).T
    adaptive_ob = adaptive_ob.reindex(index=wt1_aligned.index, columns=wt1_aligned.columns)
    in_zone = (wt1_aligned >= 40) & (wt1_aligned <= adaptive_ob)
    signals = in_zone & came_from_below
    return signals.reindex(index=mcap_df.index, columns=wt1_df.columns)


def run_backtest(prices_df, wt1_df, mcap_df, signals_df, n_hold=10, start=None):
    """月度调仓: 每月末选 top-N (按 wt1 排名), 持有到次月"""
    # 对齐 wt1 / signals 到 prices 索引
    wt1_df = wt1_df.reindex(prices_df.index)
    signals_df = signals_df.reindex(prices_df.index)

    if start is not None:
        mask = prices_df.index >= pd.Timestamp(start)
        prices_df = prices_df[mask]
        wt1_df = wt1_df[mask]
        signals_df = signals_df[mask]

    dates = prices_df.index
    rets = prices_df.pct_change().fillna(0)

    # 组合净值
    nav = 1.0
    nav_series = []
    selected_last = []

    for i in range(len(dates)):
        if i == 0:
            nav_series.append(nav)
            continue
        dt = dates[i]
        # 用上月信号 + wt1 排名选股
        if i - 1 >= 0:
            sig_month = signals_df.iloc[i - 1]
            wt_month = wt1_df.iloc[i - 1]

            # 候选 = 信号触发且非 NaN
            candidates = sig_month.fillna(False)
            valid = candidates & wt_month.notna()

            if valid.sum() > 0:
                # 在 valid 中按 wt1 排名选 top-N
                ranked = wt_month[valid].rank(ascending=False)
                selected = ranked.nsmallest(n_hold).index.tolist()
            else:
                selected = []
            selected_last = selected

        # 本月收益
        if selected_last:
            month_rets = rets.iloc[i][selected_last].dropna()
            if len(month_rets) > 0:
                nav *= (1 + month_rets.mean())
        nav_series.append(nav)

    return pd.Series(nav_series, index=dates), nav_series[-1]


def run_bh(prices_df, mcap_df, n_hold=10, start=None):
    """买入持有 benchmark: 每月初持等权 top-N 市值 (避免全市场含退市股归零)"""
    if start is not None:
        mask = prices_df.index >= pd.Timestamp(start)
        prices_df = prices_df[mask]
        mcap_df = mcap_df[mask]
    rets = prices_df.pct_change().fillna(0)
    nav = 1.0
    nav_series = []
    selected_last = []

    for i in range(len(rets)):
        if i == 0:
            nav_series.append(1.0)
            continue
        if i - 1 >= 0:
            mc = mcap_df.iloc[i - 1]
            valid = mc.notna()
            if valid.sum() > 0:
                ranked = mc[valid].rank(ascending=False)
                selected_last = ranked.nsmallest(n_hold).index.tolist()
            else:
                selected_last = []
        if selected_last:
            month_rets = rets.iloc[i][selected_last].dropna()
            if len(month_rets) > 0:
                nav *= (1 + month_rets.mean())
        nav_series.append(nav)
    return pd.Series(nav_series, index=rets.index), nav_series[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n-hold', type=int, default=10)
    ap.add_argument('--start', default='2012-01-31')
    ap.add_argument('--out-dir', default=str(Path(__file__).parent))
    ap.add_argument('--h5', default=str(DEFAULT_H5))
    args = ap.parse_args()

    print(f"🔬 BT-010 — BUY_LADDER v3.1 对比回测 ({datetime.now().date()})")
    print(f"   数据: {args.h5}")
    print(f"   start: {args.start}, n_hold: {args.n_hold}")
    print("=" * 72)

    data = load_v21_data(args.h5)
    prices = data['prices']
    wt1 = data['wt1_monthly']
    mcap = data['market_cap']

    print(f"   prices: {prices.shape}, wt1: {wt1.shape}, mcap: {mcap.shape}")
    print(f"   wt1 NaN 比例: {wt1.isna().mean().mean()*100:.1f}%")

    # 对齐列
    common_cols = prices.columns.intersection(wt1.columns).intersection(mcap.columns)
    prices = prices[common_cols]
    wt1 = wt1[common_cols]
    mcap = mcap[common_cols]
    print(f"   对齐后标的: {len(common_cols)}")

    # C1 信号
    c1 = detect_c1_signals(wt1)
    c2 = detect_c2_signals(wt1, mcap)

    print(f"\n[信号触发统计]")
    print(f"  C1 (经典 [40,60]): {c1.sum().sum()} 次触发")
    print(f"  C2 (V21 adaptive OB): {c2.sum().sum()} 次触发")

    # 运行 3 种配置
    print(f"\n[回测运行]")
    c1_nav, c1_final = run_backtest(prices, wt1, mcap, c1, args.n_hold, args.start)
    print(f"  C1 经典: NAV={c1_final:.3f} ({((c1_final-1)*100):+.1f}%)")
    c2_nav, c2_final = run_backtest(prices, wt1, mcap, c2, args.n_hold, args.start)
    print(f"  C2 V21 OB: NAV={c2_final:.3f} ({((c2_final-1)*100):+.1f}%)")
    c3_nav, c3_final = run_bh(prices, mcap, args.n_hold, args.start)
    print(f"  C3 买入持有: NAV={c3_final:.3f} ({((c3_final-1)*100):+.1f}%)")

    # 汇总
    print(f"\n{'='*72}")
    print("📊 对比结果")
    print(f"{'='*72}")
    print(f"{'配置':<20} {'NAV':>10} {'区间收益':>12} {'触发次数':>10}")
    print(f"{'-'*60}")
    print(f"{'C1 经典 [40,60]':<20} {c1_final:>10.3f} {((c1_final-1)*100):>+11.1f}% {int(c1.sum().sum()):>10}")
    print(f"{'C2 V21 OB':<20} {c2_final:>10.3f} {((c2_final-1)*100):>+11.1f}% {int(c2.sum().sum()):>10}")
    print(f"{'C3 买入持有':<20} {c3_final:>10.3f} {((c3_final-1)*100):>+11.1f}% {'-':>10}")

    # 保存
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        'date': c1_nav.index,
        'c1_classic': c1_nav.values,
        'c2_v21ob': c2_nav.values,
        'c3_bh': c3_nav.values,
    }).to_csv(out_dir / 'results_by_variant.csv', index=False)

    summary = {
        'date': str(datetime.now().date()),
        'start': args.start,
        'n_hold': args.n_hold,
        'c1_classic': {'nav': c1_final, 'ret_pct': (c1_final - 1) * 100, 'triggers': int(c1.sum().sum())},
        'c2_v21ob': {'nav': c2_final, 'ret_pct': (c2_final - 1) * 100, 'triggers': int(c2.sum().sum())},
        'c3_bh': {'nav': c3_final, 'ret_pct': (c3_final - 1) * 100},
    }
    with open(out_dir / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {out_dir}/")


if __name__ == "__main__":
    main()