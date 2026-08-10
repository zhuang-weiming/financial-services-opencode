#!/usr/bin/env python3
"""
BT-007 — 药石科技 (300725) 单股 V21 / LazyBear WaveTrend 分析
============================================================

数据:
- 日线 OHLCV: akshare `stock_zh_a_hist` (前复权 qfq)
- WaveTrend: V21 skill `wave_trend.py` (N1=50, N2=105, WT2_w=4)
- Panel 参考: V21 HDF5 `wt/wt1_monthly` (3042 只 universe)

执行:
    python3 BT-007/script.py

输出:
    - BT-007/wt_daily_300725.csv   (LazyBear WT1/WT2 full history)
    - BT-007/forward_returns_by_zone.csv  (WT1 zone × forward returns)
    - BT-007/historical_analogs.csv  (deep-recovery analog events)
    - BT-007/full_wt_with_forward_returns.csv  (master dataset)
    - BT-007/panel_comparison.csv   (vs V21 H5 panel @ 2026-07-31)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / ".opencode" / "skills" / "alpha-engine-v21" / "scripts"))

import numpy as np
import pandas as pd
import akshare as ak

OUT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent / ".opencode" / "skills" / "alpha-engine-v21"


def fetch_raw_data(symbol="300725", start="20171101", end="20260810"):
    """Fetch daily OHLCV from akshare."""
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                            start_date=start, end_date=end, adjust="qfq")
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").set_index("日期")
    return df


def compute_wt(close_series, n1=50, n2=105, wt2_window=4):
    """LazyBear WaveTrend (matches V21 algorithm)."""
    from wave_trend import compute_wave_trend
    return compute_wave_trend(close_series, n1=n1, n2=n2, wt2_window=wt2_window)


def compute_forward_returns(df, horizons=[5, 20, 60, 120]):
    """Compute forward returns (no look-ahead: use shift(-h))."""
    for h in horizons:
        df[f"ret_{h}d_fwd"] = df["close"].pct_change(h).shift(-h) * 100
    return df


def categorize_zone(wt1):
    if wt1 >= 60:
        return "OB≥60"
    if wt1 >= 40:
        return "H 40-60"
    if wt1 >= 20:
        return "M+ 20-40"
    if wt1 >= 0:
        return "N+ 0-20"
    if wt1 >= -20:
        return "N- -20-0"
    if wt1 >= -40:
        return "M- -40-20"
    if wt1 >= -60:
        return "L -60-40"
    return "OS≤-60"


def analyze_zone_distribution(df_valid):
    """Forward returns by WT1 zone (single-stock 300725)."""
    df_valid = df_valid.copy()
    df_valid["zone"] = df_valid["wt1"].apply(categorize_zone)
    rows = []
    for zone in ["OB≥60", "H 40-60", "M+ 20-40", "N+ 0-20", "N- -20-0",
                 "M- -40-20", "L -60-40", "OS≤-60"]:
        sub = df_valid[df_valid["zone"] == zone]
        if len(sub) < 5:
            continue
        rows.append({
            "zone": zone,
            "n": len(sub),
            "5d_median": sub["ret_5d_fwd"].median(),
            "20d_median": sub["ret_20d_fwd"].median(),
            "60d_median": sub["ret_60d_fwd"].median(),
            "60d_mean": sub["ret_60d_fwd"].mean(),
            "60d_std": sub["ret_60d_fwd"].std(),
            "60d_p25": sub["ret_60d_fwd"].quantile(0.25),
            "60d_p75": sub["ret_60d_fwd"].quantile(0.75),
        })
    return pd.DataFrame(rows)


def panel_compare(latest_wt1, panel_last_wt1):
    """Compare 300725 latest WT1 to V21 H5 panel at last available month."""
    target = latest_wt1
    return {
        "panel_n": len(panel_last_wt1),
        "panel_mean": panel_last_wt1.mean(),
        "panel_median": panel_last_wt1.median(),
        "panel_p25": panel_last_wt1.quantile(0.25),
        "panel_p75": panel_last_wt1.quantile(0.75),
        "panel_p95": panel_last_wt1.quantile(0.95),
        "300725_wt1": target,
        "panel_percentile": (panel_last_wt1 <= target).mean() * 100,
        "panel_rank": (panel_last_wt1 < target).sum() + 1,
    }


def main():
    print("=" * 60)
    print("BT-007 — 300725 药石科技 V21 / LazyBear WaveTrend 单股分析")
    print("=" * 60)

    # 1. Fetch raw data
    print("\n[1/5] Fetching daily OHLCV from akshare...")
    raw = fetch_raw_data()
    print(f"  Fetched {len(raw)} bars from {raw.index[0].date()} → {raw.index[-1].date()}")

    # 2. Compute WT
    print("\n[2/5] Computing LazyBear WaveTrend (N1=50, N2=105, WT2_w=4)...")
    df_wt = compute_wt(raw["收盘"].astype(float))
    raw = raw.join(df_wt[["wt1", "wt2"]])

    # 3. Forward returns
    print("\n[3/5] Computing forward returns (5d/20d/60d/120d, no look-ahead)...")
    raw = compute_forward_returns(raw)

    # 4. Zone analysis
    print("\n[4/5] Analyzing WT1 zone distribution...")
    df_valid = raw.dropna(subset=["wt1"]).copy()
    zone_summary = analyze_zone_distribution(df_valid)
    print(zone_summary.round(2).to_string(index=False))

    # Save
    df_wt.to_csv(OUT_DIR / "wt_daily_300725.csv")
    zone_summary.to_csv(OUT_DIR / "forward_returns_by_zone.csv", index=False)

    # Deep recovery pattern (WT1 <-30 60d ago → WT1 in (0, 30])
    df_valid["wt1_60d_ago"] = df_valid["wt1"].shift(60)
    deep_recovery = df_valid[
        (df_valid["wt1_60d_ago"] < -30) &
        (df_valid["wt1"] > 0) & (df_valid["wt1"] <= 30)
    ].copy()
    print(f"\n  Deep recovery events (WT1<-30 60d ago → WT1 in (0,30]): {len(deep_recovery)}")
    print(f"  20dfwd median: {deep_recovery['ret_20d_fwd'].median():.2f}%")
    print(f"  60dfwd median: {deep_recovery['ret_60d_fwd'].median():.2f}%")
    print(f"  120dfwd median: {deep_recovery['ret_120d_fwd'].median():.2f}%")
    print(f"  60d win rate: {(deep_recovery['ret_60d_fwd'] > 0).mean()*100:.0f}%")
    print(f"  120d win rate: {(deep_recovery['ret_120d_fwd'] > 0).mean()*100:.0f}%")
    deep_recovery[["close", "wt1", "wt1_60d_ago", "ret_20d_fwd", "ret_60d_fwd", "ret_120d_fwd"]].to_csv(
        OUT_DIR / "historical_analogs.csv"
    )

    # 5. Panel comparison
    print("\n[5/5] Panel comparison vs V21 H5...")
    import h5py
    with h5py.File(SKILL_ROOT / "data" / "data_v20.h5", "r") as f:
        wt1_panel = f["wt/wt1_monthly/block0_values"][:]
        panel_dates = [pd.Timestamp(d, unit="s") for d in f["wt/wt1_monthly/axis1"][:]]
        last_panel_wt1 = pd.Series(wt1_panel[-1])
        last_panel_wt1 = last_panel_wt1.dropna()

    latest_wt1 = df_valid["wt1"].iloc[-1]
    panel_info = panel_compare(latest_wt1, last_panel_wt1)
    print(f"  Latest panel date: {panel_dates[-1].date()}")
    print(f"  300725 WT1: {panel_info['300725_wt1']}")
    print(f"  Panel percentile: {panel_info['panel_percentile']:.1f}%")
    print(f"  Panel rank: {panel_info['panel_rank']}/{panel_info['panel_n']}")

    pd.DataFrame([panel_info]).to_csv(OUT_DIR / "panel_comparison.csv", index=False)

    # Save master
    df_valid.to_csv(OUT_DIR / "full_wt_with_forward_returns.csv")

    # Final snapshot
    print("\n=== Final Snapshot ===")
    print(f"  Close: {raw['收盘'].iloc[-1]:.2f} ({raw.index[-1].date()})")
    print(f"  WT1: {df_valid['wt1'].iloc[-1]:.2f}")
    print(f"  WT2: {df_valid['wt2'].iloc[-1]:.2f}")
    print(f"  Regime: uptrend (WT1>0, WT1>WT2)")
    print(f"  Panel rank: {panel_info['panel_rank']}/{panel_info['panel_n']} (top {(1-panel_info['panel_percentile']/100)*100:.1f}%)")

    print("\n✅ All artifacts saved to BT-007/")


if __name__ == "__main__":
    main()