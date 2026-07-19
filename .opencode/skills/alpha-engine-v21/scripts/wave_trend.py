"""wave_trend.py — Single-stock WaveTrend (LazyBear) indicator calculator.

Two modes:

  1. **Compute** mode (default): Compute WT1 / WT2 from a price series.
     LazyBear WaveTrend algorithm:

         ESA  = EMA(close, N1)          # N1 = 10 weeks = 50 trading days
         D    = EMA(|close - ESA|, N1)
         CI   = (close - ESA) / (0.015 * D)
         WT1  = EMA(CI, N2)             # N2 = 21 weeks = 105 trading days
         WT2  = SMA(WT1, 4)             # signal line

  2. **H5 lookup** mode (``--from-h5``): Read the pre-computed monthly
     WT1 / WT2 stored in the bundled V21 HDF5. Useful for consistency checks
     against the backtest, since V21 selects stocks based on these H5 values.

⚠️  **PRINCIPLE — FULL-HISTORY COMPUTATION** ⚠️
    WaveTrend MUST be computed from the **stock's entire available price
    history, starting at the listing date**, NOT from a recent window like
    "last 12 months" or "last 5 years". The EMA structure (N2 = 105 trading
    days = ~21 weeks of half-life) is designed to capture multi-month
    momentum regimes; truncating the input series biases the oscillator
    toward short-term noise and breaks the cross-sectional comparability
    that V21's selection logic depends on.

    When you pass ``--csv`` / compute from a Series, give the function the
    full history (e.g. daily closes from IPO to today). When you pass
    ``--from-h5``, the H5 already stores WT1 computed from each stock's
    full pre-bundled price history (1990-12-31 → 2026-07-31, depending on
    listing date).

    The summary fields ``wt1_pct_rank_12m`` / ``wt1_pct_rank_5y`` in the JSON
    output are **descriptive context only** (where does current WT1 sit
    relative to recent history?) — they are NOT the WT1 calculation itself.

Usage examples:

    # Compute from a CSV (date, close) — pass the FULL history from listing!
    python wave_trend.py --csv prices.csv --ticker MYSTOCK --plot

    # Look up from H5 (already pre-computed from full history)
    python wave_trend.py --ticker 600519-CN --from-h5

    # Custom parameters
    python wave_trend.py --csv prices.csv --ticker MYSTOCK --n1 50 --n2 105

Output: stdout JSON (or CSV via --csv-out). Optional matplotlib plot.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

DEFAULT_N1 = 50
DEFAULT_N2 = 105
DEFAULT_WT2_WINDOW = 4


# ==============================================================================
# LazyBear WaveTrend computation
# ==============================================================================


def compute_wave_trend(
    close: pd.Series,
    n1: int = DEFAULT_N1,
    n2: int = DEFAULT_N2,
    wt2_window: int = DEFAULT_WT2_WINDOW,
) -> pd.DataFrame:
    """Compute LazyBear WaveTrend from a close-price Series.

    ⚠️ **Full-history principle**: this function uses the **entire price
    Series** you pass in — from the first row (typically the listing date)
    to the last row (typically today). Do NOT pre-truncate to a recent
    window like "last 12 months"; the EMA structure (N2 = 105 trading
    days) depends on long-history context to produce stable, comparable
    WT1 values across the cross-section.

    Args:
        close: pd.Series indexed by datetime, **from the stock's listing
            date onwards** (any frequency; resample first if needed). Must
            have at least n1 + n2 + wt2_window observations for stable
            output.
        n1: EMA span for ESA/D (default 50 = ~10 trading weeks).
        n2: EMA span for WT1 (default 105 = ~21 trading weeks).
        wt2_window: SMA window for WT2 signal line (default 4).

    Returns:
        DataFrame with columns [close, esa, d, ci, wt1, wt2].
        NaN for warm-up bars (first max(n1, n2) + wt2_window observations);
        stable values from there onwards.
    """
    close = pd.Series(close).astype(float).dropna()
    if len(close) < max(n1, n2) + wt2_window:
        raise ValueError(
            f"need at least {max(n1, n2) + wt2_window} observations from "
            f"listing date onwards, got {len(close)}. Pass the FULL history, "
            f"not a recent window."
        )

    esa = close.ewm(span=n1, adjust=False).mean()
    d = (close - esa).abs().ewm(span=n1, adjust=False).mean()
    d_safe = d.replace(0, np.nan)
    ci = (close - esa) / (0.015 * d_safe)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(wt2_window).mean()

    return pd.DataFrame(
        {
            "close": close,
            "esa": esa,
            "d": d,
            "ci": ci,
            "wt1": wt1,
            "wt2": wt2,
        }
    )


def summarise(df: pd.DataFrame) -> dict:
    """Latest-bar + percentile summary of a WaveTrend DataFrame.

    The ``wt1_pct_rank_*`` fields are **descriptive context only** — they
    show where current WT1 sits relative to recent history. They are NOT
    the WT1 calculation itself; that computation always uses the full
    price series passed in (see compute_wave_trend docstring).
    """
    last = df.dropna(subset=["wt1", "wt2"]).iloc[-1]
    last_date = df.dropna(subset=["wt1", "wt2"]).index[-1]
    wt1_clean = df["wt1"].dropna()
    wt2_clean = df["wt2"].dropna()
    return {
        "as_of": str(last_date),
        "wt1": round(float(last["wt1"]), 2),
        "wt2": round(float(last["wt2"]), 2),
        # Descriptive only — relative position of current WT1 vs history.
        # The WT1 value itself is computed from full-history input, see above.
        "wt1_pct_rank_12m": round(
            float((wt1_clean.iloc[-252:] <= last["wt1"]).mean() * 100), 1
        )
        if len(wt1_clean) >= 252
        else None,
        "wt1_pct_rank_5y": round(
            float((wt1_clean <= last["wt1"]).mean() * 100), 1
        )
        if len(wt1_clean) > 0
        else None,
        "wt1_min": round(float(wt1_clean.min()), 2),
        "wt1_max": round(float(wt1_clean.max()), 2),
        "wt1_mean": round(float(wt1_clean.mean()), 2),
        "wt2_min": round(float(wt2_clean.min()), 2),
        "wt2_max": round(float(wt2_clean.max()), 2),
        "regime": _regime(last["wt1"], last["wt2"]),
    }


def _regime(wt1: float, wt2: float) -> str:
    """Classify the latest bar into one of four LazyBear regimes.

    > +60  : strongly overbought — momentum extended
    > 0 with WT1 > WT2 : uptrend
    < 0 with WT1 < WT2 : downtrend
    cross of WT2      : signal event
    """
    if wt1 > 60:
        return "overbought"
    if wt1 > 0 and wt1 > wt2:
        return "uptrend"
    if wt1 < 0 and wt1 < wt2:
        return "downtrend"
    return "transition"


# ==============================================================================
# H5 lookup
# ==============================================================================


def lookup_h5_wt(
    ticker: str,
    data: Optional[dict] = None,
) -> pd.DataFrame:
    """Read pre-computed monthly WT1 / WT2 from the bundled HDF5.

    Args:
        ticker: Ticker symbol, e.g. "600519-CN". The suffix "-CN" is added
            if not present.
        data: Pre-loaded V21 data dict (avoids re-reading the HDF5). If None,
            ``data_loader.load_v21_data()`` is called.

    Returns:
        DataFrame with columns [wt1_monthly, wt2_monthly] indexed by month-end.
    """
    if data is None:
        from data_loader import load_v21_data  # noqa: WPS433 (delayed import)

        data = load_v21_data()

    sym = ticker if ticker.endswith("-CN") else ticker + "-CN"
    wt1 = data["wt1_monthly"]
    wt2 = data.get("wt2_monthly")
    if sym not in wt1.columns:
        raise KeyError(
            f"{sym} not in V21 HDF5 universe ({len(wt1.columns)} stocks available)"
        )
    out = pd.DataFrame({"wt1_monthly": wt1[sym]})
    if wt2 is not None and sym in wt2.columns:
        out["wt2_monthly"] = wt2[sym]
    out.index.name = "month"
    return out


# ==============================================================================
# CLI
# ==============================================================================


def _read_prices_csv(path: str, ticker_label: Optional[str] = None) -> pd.Series:
    """Read a close-price CSV. Accepts either ``date,close`` or
    ``date,open,high,low,close,volume`` (Yahoo format)."""
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    if "date" not in df.columns:
        if "datetime" in df.columns:
            df = df.rename(columns={"datetime": "date"})
        else:
            df = df.rename(columns={df.columns[0]: "date"})
    if "close" not in df.columns:
        raise ValueError(f"CSV must contain a 'close' column: {df.columns.tolist()}")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    return df["close"].astype(float)


def _maybe_plot(df: pd.DataFrame, ticker: str, out_path: Optional[str]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[plot] matplotlib not installed — skipping plot", file=sys.stderr)
        return
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    axes[0].plot(df.index, df["close"], color="black", lw=1, label="close")
    axes[0].set_title(f"{ticker} close")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)

    axes[1].plot(df.index, df["wt1"], color="#1f77b4", lw=1, label="WT1")
    axes[1].plot(df.index, df["wt2"], color="#ff7f0e", lw=1, label="WT2")
    axes[1].axhline(0, color="grey", lw=0.5, ls="--")
    axes[1].axhline(60, color="red", lw=0.5, ls="--", alpha=0.5, label="OB=60")
    axes[1].axhline(-60, color="green", lw=0.5, ls="--", alpha=0.5, label="OS=-60")
    axes[1].set_title(f"{ticker} WaveTrend (LazyBear, N1=50, N2=105)")
    axes[1].legend(loc="upper left")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=120)
        print(f"[plot] saved → {out_path}", file=sys.stderr)
    else:
        plt.show()
    plt.close(fig)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Compute or look up LazyBear WaveTrend for a single ticker."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", type=str, help="CSV path with date,close columns")
    src.add_argument(
        "--from-h5",
        action="store_true",
        help="Read pre-computed monthly WT1/WT2 from bundled HDF5",
    )
    p.add_argument(
        "--ticker",
        type=str,
        required=True,
        help="Ticker label (any string for CSV mode; 600519-CN for H5 mode)",
    )
    p.add_argument("--n1", type=int, default=DEFAULT_N1, help="ESA EMA span (default 50)")
    p.add_argument("--n2", type=int, default=DEFAULT_N2, help="WT1 EMA span (default 105)")
    p.add_argument(
        "--wt2-window", type=int, default=DEFAULT_WT2_WINDOW, help="WT2 SMA window"
    )
    p.add_argument("--csv-out", type=str, help="Optional path to save full series as CSV")
    p.add_argument("--plot", action="store_true", help="Render matplotlib chart")
    p.add_argument("--plot-out", type=str, help="If set with --plot, save PNG to this path")
    p.add_argument(
        "--tail",
        type=int,
        default=24,
        help="When --csv-out is set, only the last N rows are written (0=all)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON summary (default: human-readable text)",
    )
    args = p.parse_args(argv)

    if args.from_h5:
        df = lookup_h5_wt(args.ticker)
        out = {
            "ticker": args.ticker if args.ticker.endswith("-CN") else args.ticker + "-CN",
            "source": "v21_h5_monthly",
            "n_obs": int(len(df)),
            "first_month": str(df.index[0].date()),
            "last_month": str(df.index[-1].date()),
            "latest": {
                "wt1_monthly": (
                    round(float(df["wt1_monthly"].iloc[-1]), 2)
                    if pd.notna(df["wt1_monthly"].iloc[-1])
                    else None
                ),
                "wt2_monthly": (
                    round(float(df["wt2_monthly"].iloc[-1]), 2)
                    if "wt2_monthly" in df and pd.notna(df["wt2_monthly"].iloc[-1])
                    else None
                ),
            },
        }
        if args.json:
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            print(f"--- {out['ticker']} (V21 H5 monthly WT) ---")
            for k, v in out.items():
                if k != "ticker":
                    print(f"  {k}: {v}")
        if args.csv_out:
            tail = df if args.tail <= 0 else df.tail(args.tail)
            tail.to_csv(args.csv_out)
            print(f"[csv-out] {args.csv_out} ({len(tail)} rows)", file=sys.stderr)
        return 0

    close = _read_prices_csv(args.csv, ticker_label=args.ticker)
    n_input = len(close)
    first_input_date = close.index[0].date() if n_input else None
    last_input_date = close.index[-1].date() if n_input else None
    span_days = (close.index[-1] - close.index[0]).days if n_input >= 2 else 0
    print(
        f"[input] {n_input} bars  span: {first_input_date} → {last_input_date}  "
        f"({span_days} days)",
        file=sys.stderr,
    )
    print(
        f"[input] full-history principle: WT uses every bar from listing → today.",
        file=sys.stderr,
    )
    df = compute_wave_trend(
        close, n1=args.n1, n2=args.n2, wt2_window=args.wt2_window
    )
    summary = summarise(df)
    summary["ticker"] = args.ticker
    summary["source"] = f"computed_n1_{args.n1}_n2_{args.n2}"
    summary["n_obs"] = int(len(df))
    summary["first_input_date"] = str(first_input_date)
    summary["last_input_date"] = str(last_input_date)
    summary["input_span_days"] = span_days

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"--- {args.ticker} WaveTrend (LazyBear, N1={args.n1}, N2={args.n2}) ---")
        for k, v in summary.items():
            print(f"  {k}: {v}")

    if args.csv_out:
        tail = df if args.tail <= 0 else df.tail(args.tail)
        tail.to_csv(args.csv_out)
        print(f"[csv-out] {args.csv_out} ({len(tail)} rows)", file=sys.stderr)
    if args.plot:
        _maybe_plot(df, args.ticker, args.plot_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
