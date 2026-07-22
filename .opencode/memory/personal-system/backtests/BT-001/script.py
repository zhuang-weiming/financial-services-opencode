"""BT-001: 极值 WT1 信号下的 A 股 forward 收益分布验证。

研究问题
--------
当前观察：
- 科技股（中微/华创/江丰/长川/拓荆）WT1 在 +70 ~ +88 (92%+ 百分位)
- 白酒股（茅台/五粮液/汾酒/泸州老窖）WT1 在 -60 ~ -78 (2-3% 百分位)

假设：当某只股票或行业板块的 WT1 达到这种极端分位时，
1/3/6 个月后的 forward 收益分布是什么样的？

方法
----
每月末（WT1 数据按月末计算）：
  - 高位组 (Hypothesis A): WT1 ≥ +60，取按 WT1 降序的前 50 只构成等权组合
  - 低位组 (Hypothesis B): WT1 ≤ -60，取按 WT1 升序的前 50 只构成等权组合
  - 对照组 (Benchmark): 全部 A 股等权组合

每月每个篮子计算 1m / 3m / 6m forward 总收益。
对每条「篮子的月度收益时间序列」统计 mean / median / std / t 检验 / bootstrap CI。

数据
----
- HDF5: .opencode/skills/alpha-engine-v21/data/data_v20.h5
- price panel: 2010-01 至 2026-07 (193 月)
- WT1 panel: 2010-01 至 2026-07 (199 月；超过价格部分无法形成 forward 收益)

诚实声明
--------
- 不发表方向性意见（不预测涨跌）。
- 不美化结果：mean / median / CI 全报，t 检验不显著也明确说。
- 价格 / WT1 / bad_returns_mask 任一项缺失则跳过该股票。
- 0.5% round-trip TC 在进场时一次性扣除（标准做空 / 做多惯例）。
- 没有 CSI 300 数据；用「全 A 等权」作为对照。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

# Make the alpha-engine-v21 scripts importable.
SKILL_ROOT = Path(
    "/Users/weimingzhuang/Documents/source_code/financial-services-opencode/"
    ".opencode/skills/alpha-engine-v21"
).resolve()
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from data_loader import load_v21_data  # noqa: E402

# ───────────────────────────────────────────────
# Config / 路径
# ───────────────────────────────────────────────
H5_PATH = SKILL_ROOT / "data" / "data_v20.h5"
OUT_DIR = Path(
    "/Users/weimingzhuang/Documents/source_code/financial-services-opencode/"
    ".opencode/memory/personal-system/backtests/BT-001"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

WT_HIGH = 60.0
WT_LOW = -60.0
TOP_N = 50
TC_ROUND_TRIP = 0.005  # 0.5% per trade (round-trip)
HORIZONS = (1, 3, 6)

# Bootstrap params
BOOT_N = 10_000
BLOCK = 12
BOOT_SEED = 42
RF_ANNUAL = 0.02

# ───────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────


def get_forward_returns(
    prices: pd.DataFrame, bm_mask: pd.DataFrame | None
) -> dict[int, pd.DataFrame]:
    """For each horizon h, return a DataFrame indexed by rebalance month t
    with columns = tickers; values = simple return from t to t+h.
    """
    out: dict[int, pd.DataFrame] = {}
    for h in HORIZONS:
        # price at t+h, divided by price at t, minus 1.
        fwd = (prices.shift(-h) / prices - 1.0).astype(float)
        # Replace ±inf with NaN — happens when denominator or numerator = 0
        # (data holes showing up as 0 in panel).
        fwd = fwd.replace([np.inf, -np.inf], np.nan)
        if bm_mask is not None:
            # ⚠ NaN → bool in Python is True. fillna FIRST then cast.
            bm_bool = bm_mask.fillna(False).astype(bool)
            # Align columns to prices.
            bm_bool = bm_bool.reindex(columns=fwd.columns, fill_value=False)
            fwd = fwd.where(~bm_bool, other=np.nan)
        out[h] = fwd
    return out


def basket_series(
    panel: pd.DataFrame,
    signal_row: pd.Series,
    horizon: int,
    high: bool,
    top_n: int,
) -> pd.Series:
    """For one signal month t, build an equal-weight basket of either
    the highest (high=True) or lowest WT1 stocks and return ONE portfolio return.
    Returns NaN if basket is empty.

    `panel` is the horizon-h forward-return DataFrame (index = month t, columns = tickers).
    `signal_row` is the WT1 Series at month t (same columns).
    """
    sig = signal_row.dropna()
    if high:
        sig = sig[sig >= WT_HIGH]
        ranked = sig.sort_values(ascending=False)
    else:
        sig = sig[sig <= WT_LOW]
        ranked = sig.sort_values(ascending=True)

    basket = ranked.head(top_n).index
    if len(basket) == 0:
        return pd.Series(np.nan, index=panel.index[:1])

    # Average across the basket. Some stocks may have NaN forward return
    # (price missing at t+h, or bad mask); ignore them per-stock.
    rets = panel.loc[panel.index[0], basket]
    return rets.mean()


def time_series_summary(
    series: pd.Series, name: str, n_configs: int = 5, tc: float = 0.0
) -> dict:
    """Statistical summary of a monthly portfolio-return time series.
    `tc` is the round-trip cost, deducted from every monthly return.
    """
    r = (series - tc).dropna()
    n = len(r)
    if n == 0:
        return {"name": name, "n": 0}

    rf_m = RF_ANNUAL / 12
    excess = r - rf_m
    mean_m = float(r.mean())
    median_m = float(r.median())
    std_m = float(r.std(ddof=1)) if n > 1 else float("nan")
    skew = float(r.skew()) if n > 2 else float("nan")
    kurt = float(r.kurtosis()) + 3 if n > 3 else float("nan")
    sharpe_m = (mean_m - rf_m) / std_m if std_m and not np.isnan(std_m) else float("nan")
    sharpe_a = sharpe_m * np.sqrt(12)

    # t-test (one-sample vs zero, no risk-free adjustment for simplicity)
    if n > 1 and not np.isnan(std_m) and std_m > 0:
        t_stat, p_two = sp_stats.ttest_1samp(r, 0.0)
    else:
        t_stat, p_two = float("nan"), float("nan")
    p_one = p_two / 2 if not np.isnan(p_two) else float("nan")

    # CAGR (geometric)
    if (1.0 + r).prod() > 0:
        cagr = (1.0 + r).prod() ** (12 / n) - 1
    else:
        cagr = float("nan")

    # Block bootstrap CI of mean monthly return
    rng = np.random.default_rng(BOOT_SEED)
    boot_means = np.empty(BOOT_N)
    arr = r.values
    if n >= BLOCK:
        for b in range(BOOT_N):
            n_blocks = int(np.ceil(n / BLOCK))
            starts = rng.integers(0, n - BLOCK + 1, size=n_blocks)
            idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
            boot_means[b] = arr[idx].mean()
    else:
        # fallback IID bootstrap
        for b in range(BOOT_N):
            boot_means[b] = rng.choice(arr, size=n, replace=True).mean()
    ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])

    # Worst 3 / best 3 single-month returns
    worst3 = r.nsmallest(3).round(4).tolist()
    best3 = r.nlargest(3).round(4).tolist()

    # Hit-rate (% positive months)
    hit = float((r > 0).mean())

    return {
        "name": name,
        "n_months": n,
        "mean_monthly": round(mean_m, 5),
        "median_monthly": round(median_m, 5),
        "std_monthly": round(std_m, 5),
        "min_monthly": round(float(r.min()), 5),
        "max_monthly": round(float(r.max()), 5),
        "median_minus_mean": round(median_m - mean_m, 5),
        "skewness": round(skew, 3),
        "kurtosis_total": round(kurt, 3),
        "sharpe_monthly": round(sharpe_m, 4),
        "sharpe_annual": round(sharpe_a, 4),
        "cagr": round(float(cagr), 4),
        "hit_rate": round(hit, 4),
        "t_stat": round(float(t_stat), 3),
        "p_two_sided": round(float(p_two), 4),
        "p_one_sided_positive": round(float(p_one), 4),
        "bootstrap_ci_95_low": round(float(ci_lo), 5),
        "bootstrap_ci_95_high": round(float(ci_hi), 5),
        "worst3_months": worst3,
        "best3_months": best3,
        "round_trip_tc": tc,
    }


def main():
    data = load_v21_data(str(H5_PATH))
    prices: pd.DataFrame = data["prices"]
    wt1: pd.DataFrame = data["wt1_monthly"]
    bm: pd.DataFrame | None = data.get("bad_returns_mask")

    print(f"[data] prices: {prices.shape}, dates {prices.index[0]} → {prices.index[-1]}")
    print(f"[data] wt1:    {wt1.shape}, dates {wt1.index[0]} → {wt1.index[-1]}")
    print(f"[data] bad_returns_mask: {'yes' if bm is not None else 'no'}")

    # ── Align timestamps: re-bucket everything to month-end.
    # prices axis1 has mixed conventions:
    #   - 2010-01-01 → 2014-12-01 (month-start)
    #   - 2015-01-31 → 2025-12-31 (month-end)
    #   - 2026-01-30 → 2026-07-03 (irregular mid-month end-of-trading)
    # Normalise all to month-end so WT1 (already month-end) aligns cleanly.
    prices.index = prices.index + pd.offsets.MonthEnd(0)
    prices = prices[~prices.index.duplicated(keep="last")].sort_index()

    # Trim WT1 to prices window
    wt1_in_window = wt1.loc[
        (wt1.index >= prices.index[0]) & (wt1.index <= prices.index[-1])
    ].copy()
    print(f"[align] prices relabeled to month-end: {prices.shape}")
    print(f"[align] WT1 restricted to price window: {wt1_in_window.shape}")

    # Tick in common
    common = sorted(set(prices.columns) & set(wt1_in_window.columns))
    print(f"[align] common tickers: {len(common)}")
    prices = prices[common]
    wt1_in_window = wt1_in_window[common]
    if bm is not None:
        bm = bm[common].reindex(prices.index)

    # ── Build forward-return panels
    fwd = get_forward_returns(prices, bm)

    # ── For each month t, build a basket and get its return
    # We only consider months where:
    #   (a) WT1 is computed at t
    #   (b) forward h-month return exists for the entire (or just any) basket universe
    common_months = sorted(set(prices.index) & set(wt1_in_window.index))
    # Take t such that prices[t+h] exists for ALL horizons
    valid_months = []
    for t in common_months:
        t_pos = prices.index.get_loc(t)
        if t_pos + max(HORIZONS) < len(prices.index):
            valid_months.append(t)
    valid_months = sorted(set(valid_months))
    print(f"[window] valid rebalance months: {len(valid_months)} "
          f"({valid_months[0] if valid_months else 'N/A'} → {valid_months[-1] if valid_months else 'N/A'})")

    # We'll iterate month-by-month and build a time series of basket returns
    high_rets: dict[int, list] = {h: [] for h in HORIZONS}
    low_rets: dict[int, list] = {h: [] for h in HORIZONS}
    universe_rets: dict[int, list] = {h: [] for h in HORIZONS}
    high_size: list = []  # number of basket stocks each month
    low_size: list = []
    months_idx: list = []

    panel_rows = []

    for t in valid_months:
        signal_row = wt1_in_window.loc[t]
        months_idx.append(t)
        # Sizes
        n_high = int((signal_row.dropna() >= WT_HIGH).sum())
        n_low = int((signal_row.dropna() <= WT_LOW).sum())
        high_size.append(min(n_high, TOP_N))
        low_size.append(min(n_low, TOP_N))

        for h in HORIZONS:
            fwd_row = fwd[h].loc[t]

            # High basket
            sig_hi = signal_row.dropna()
            sig_hi = sig_hi[sig_hi >= WT_HIGH].sort_values(ascending=False)
            basket_hi = sig_hi.head(TOP_N).index
            r_hi = fwd_row[basket_hi].dropna().mean() if len(basket_hi) else np.nan

            # Low basket
            sig_lo = signal_row.dropna()
            sig_lo = sig_lo[sig_lo <= WT_LOW].sort_values(ascending=True)
            basket_lo = sig_lo.head(TOP_N).index
            r_lo = fwd_row[basket_lo].dropna().mean() if len(basket_lo) else np.nan

            # Universe basket
            universe_rets_series = fwd_row.dropna()
            r_uni = universe_rets_series.mean() if len(universe_rets_series) else np.nan

            high_rets[h].append(r_hi)
            low_rets[h].append(r_lo)
            universe_rets[h].append(r_uni)

            panel_rows.append({
                "month": t,
                "horizon_months": h,
                "signal": "high_wt1",
                "n_basket": min(n_high, TOP_N),
                "basket_return": r_hi,
                "universe_return": r_uni,
            })
            panel_rows.append({
                "month": t,
                "horizon_months": h,
                "signal": "low_wt1",
                "n_basket": min(n_low, TOP_N),
                "basket_return": r_lo,
                "universe_return": r_uni,
            })

    # ── Build time-series
    idx = pd.DatetimeIndex(months_idx)
    high_ts = {h: pd.Series(high_rets[h], index=idx) for h in HORIZONS}
    low_ts = {h: pd.Series(low_rets[h], index=idx) for h in HORIZONS}
    uni_ts = {h: pd.Series(universe_rets[h], index=idx) for h in HORIZONS}

    # ── Summary statistics — raw and TC-adjusted
    results: list[dict] = []
    for h in HORIZONS:
        for label, ts, side in [
            ("high_wt1_top50",  high_ts[h], "high"),
            ("low_wt1_bottom50", low_ts[h],  "low"),
            ("all_a_share_eqw", uni_ts[h],  "benchmark"),
        ]:
            for tc, tc_label in [(0.0, "no_tc"), (TC_ROUND_TRIP, "tc_0.5pct")]:
                results.append(time_series_summary(ts, f"{label}_h{h}m_{tc_label}", tc=tc))

    # ── Long-short (high minus low) series
    ls_rets: dict[int, pd.Series] = {
        h: high_ts[h] - low_ts[h] for h in HORIZONS
    }
    for h in HORIZONS:
        for tc, tc_label in [(0.0, "no_tc"), (2 * TC_ROUND_TRIP, "tc_2x")]:
            # long-short pays twice: long entry + short entry (or equivalently
            # we model short-selling cost). 2 × round-trip.
            results.append(time_series_summary(
                ls_rets[h], f"long_short_high_minus_low_h{h}m_{tc_label}", tc=tc
            ))

    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUT_DIR / "results.csv", index=False)
    print(f"[save] results.csv ({len(results_df)} rows)")

    # Save panel
    panel_df = pd.DataFrame(panel_rows)
    panel_df.to_csv(OUT_DIR / "panel.csv", index=False)
    print(f"[save] panel.csv ({len(panel_df)} rows)")

    # ── Per-hypothesis event count
    n_high_events = sum(int(x > 0) for x in high_size)
    n_low_events = sum(int(x > 0) for x in low_size)
    print(f"[counts] months with >=1 high basket: {n_high_events}/{len(months_idx)}")
    print(f"[counts] months with >=1 low basket:  {n_low_events}/{len(months_idx)}")
    print(f"[counts] avg basket size (high): {np.mean(high_size):.1f}")
    print(f"[counts] avg basket size (low):  {np.mean(low_size):.1f}")

    # ── Sub-period analysis (2010-2014, 2015-2019, 2020-2026)
    sub_rows = []
    sub_periods = [
        ("2010-2014",  "2010-01-01", "2014-12-31"),
        ("2015-2019",  "2015-01-01", "2019-12-31"),
        ("2020-2026",  "2020-01-01", "2026-12-31"),
    ]
    for period_name, start, end in sub_periods:
        mask = (idx >= start) & (idx <= end)
        for h in HORIZONS:
            for sig_lbl, ts in [
                ("high_wt1_top50",  high_ts[h]),
                ("low_wt1_bottom50", low_ts[h]),
                ("all_a_share_eqw", uni_ts[h]),
                ("long_short",      ls_rets[h]),
            ]:
                sub = ts.loc[mask].dropna()
                if len(sub) < 5:
                    continue
                if sig_lbl == "long_short":
                    tc_use = 2 * TC_ROUND_TRIP if tc_label == "tc_2x" else 0.0
                else:
                    tc_use = TC_ROUND_TRIP if tc_label == "tc_0.5pct" else 0.0
                sub_rows.append({
                    "period": period_name,
                    "horizon_months": h,
                    "signal": sig_lbl,
                    "tc": tc_use,
                    "n": len(sub),
                    "mean_monthly": round(float(sub.mean()), 5),
                    "median_monthly": round(float(sub.median()), 5),
                    "std_monthly": round(float(sub.std(ddof=1)), 5),
                    "hit_rate": round(float((sub > 0).mean()), 4),
                })
    sub_df = pd.DataFrame(sub_rows)
    sub_df.to_csv(OUT_DIR / "subperiods.csv", index=False)
    print(f"[save] subperiods.csv ({len(sub_df)} rows)")

    # ── Print headline numbers
    print("\n" + "=" * 78)
    print(f"BASIS: {len(months_idx)} months ({months_idx[0]} → {months_idx[-1]})")
    print("=" * 78)
    for h in HORIZONS:
        print(f"\n--- Horizon = {h}m ---")
        for tc_lbl in ["no_tc", "tc_0.5pct"]:
            for sig_lbl in ["high_wt1_top50", "low_wt1_bottom50", "all_a_share_eqw"]:
                row = results_df[
                    (results_df["name"] == f"{sig_lbl}_h{h}m_{tc_lbl}")
                ].iloc[0]
                print(
                    f"  {row['name']:<35s} "
                    f"n={row['n_months']:>3d}  "
                    f"mean={row['mean_monthly']*100:+.2f}%  "
                    f"median={row['median_monthly']*100:+.2f}%  "
                    f"std={row['std_monthly']*100:.2f}%  "
                    f"CI95=[{row['bootstrap_ci_95_low']*100:+.2f}%, "
                    f"{row['bootstrap_ci_95_high']*100:+.2f}%]  "
                    f"p(one-sided>+0)={row['p_one_sided_positive']:.3f}  "
                    f"hit={row['hit_rate']*100:.0f}%"
                )

    # ── Long-short spread
    print(f"\n--- Long-short (high - low, equal-weight) ---")
    for h in HORIZONS:
        for tc_lbl in ["no_tc", "tc_2x"]:
            row = results_df[
                (results_df["name"] == f"long_short_high_minus_low_h{h}m_{tc_lbl}")
            ].iloc[0]
            print(
                f"  {row['name']:<45s} "
                f"n={row['n_months']:>3d}  "
                f"mean={row['mean_monthly']*100:+.2f}%  "
                f"median={row['median_monthly']*100:+.2f}%  "
                f"std={row['std_monthly']*100:.2f}%  "
                f"CI95=[{row['bootstrap_ci_95_low']*100:+.2f}%, "
                f"{row['bootstrap_ci_95_high']*100:+.2f}%]  "
                f"hit={row['hit_rate']*100:.0f}%"
            )

    # ── Sub-period table
    print(f"\n--- Sub-period (no TC) ---")
    pivot = sub_df[(sub_df["tc"] == 0.0)].pivot_table(
        index=["signal", "horizon_months"],
        columns="period",
        values="mean_monthly",
    )
    print(pivot.round(4))
    print(f"\n--- Sub-period (no TC, MEDIAN) ---")
    pivot_med = sub_df[(sub_df["tc"] == 0.0)].pivot_table(
        index=["signal", "horizon_months"],
        columns="period",
        values="median_monthly",
    )
    print(pivot_med.round(4))

    # ── JSON dump for programmatic consumers
    headline = {
        "window": {
            "first_month": str(months_idx[0]),
            "last_month": str(months_idx[-1]),
            "n_months": len(months_idx),
        },
        "signal_thresholds": {"high": WT_HIGH, "low": WT_LOW, "top_n": TOP_N},
        "horizons_months": list(HORIZONS),
        "tc_round_trip": TC_ROUND_TRIP,
        "results": results,
        "subperiods": sub_rows,
        "data_quality": {
            "n_prices_tickers": int(prices.shape[1]),
            "n_wt1_tickers": int(wt1_in_window.shape[1]),
            "n_common_tickers": int(prices.shape[1]),
            "n_rebalance_months": len(months_idx),
            "avg_high_basket_size": float(np.mean(high_size)),
            "avg_low_basket_size": float(np.mean(low_size)),
            "months_with_high_signal": int(n_high_events),
            "months_with_low_signal": int(n_low_events),
            "h5_path": str(H5_PATH),
        },
    }
    (OUT_DIR / "results.json").write_text(
        json.dumps(headline, indent=2, ensure_ascii=False, default=str)
    )
    print(f"[save] results.json")


if __name__ == "__main__":
    main()
