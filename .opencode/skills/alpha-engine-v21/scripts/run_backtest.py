#!/usr/bin/env python3
"""run_backtest.py — V21 production backtest runner.

Single CLI for the alpha-engine-v21 skill. Produces:

    results/equity_v21.csv         monthly NAV curve
    results/trades_v21.csv         rebalance log with stock names + industry
    results/v21_authoritative_results.json   metrics + statistical battery + sub-samples

Usage:
    python3 run_backtest.py                       # full backtest (TC on by default)
    python3 run_backtest.py --periods             # full + sub-samples + IS/OOS
    python3 run_backtest.py --walkforward         # full + rolling walk-forward OOS
    python3 run_backtest.py --periods --walkforward
    python3 run_backtest.py --no-tc               # opt out of TC modelling (TC off)
    python3 run_backtest.py --data-path /custom/path/data_v20.h5
    python3 run_backtest.py --help

V21 default configuration is loaded from config/v21_config.json (single source
of truth). Path resolution: --data-path > $V21_DATA_H5 > config.json > bundled
data_v20.h5. See data_loader.resolve_data_path() for full chain.
"""
import argparse
import json
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from alpha_engine import (  # noqa: E402
    BacktestConfig,
    run_backtest,
    score_v21,
)
from data_loader import load_v21_data  # noqa: E402
from statistical_tests import honest_statistical_tests  # noqa: E402

RESULTS_DIR = SKILL_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)
CONFIG_PATH = SKILL_ROOT / "config" / "v21_config.json"


# ==============================================================================
# Config loading
# ==============================================================================


def load_v21_config(path: Path, no_tc: bool = False) -> BacktestConfig:
    """Build BacktestConfig from config/v21_config.json.

    Args:
        path: Path to v21_config.json.
        no_tc: If True, force ``transaction_cost=False`` regardless of JSON.

    Returns:
        BacktestConfig instance.
    """
    with open(path) as f:
        cfg = json.load(f)
    w = cfg["weights"]
    required = {"lv", "wt_mom"}
    if set(w.keys()) != required:
        raise ValueError(
            f"v21_config.json weights must be exactly {required}, got {set(w.keys())}"
        )
    tc_default = cfg.get("transaction_cost", True)
    return BacktestConfig(
        name=cfg.get("name", "V21"),
        n_hold=cfg.get("n_hold", 10),
        max_per_ind=cfg.get("max_per_ind", 3),
        liq_filter_mcap=cfg.get("liq_filter_mcap", 2e9),
        ob_filter=cfg.get("ob_filter", True),
        bad_return_threshold=cfg.get("bad_return_threshold", 0.40),
        ob_base=cfg.get("ob_base", 53),
        ob_cap_adj=cfg.get("ob_cap_adj", 40),
        warmup=cfg.get("warmup", 4),
        transaction_cost=(False if no_tc else tc_default),
    )


# ==============================================================================
# Output helpers
# ==============================================================================


def trades_to_csv(trades, out_path, data=None):
    if not trades:
        print(f"[out] No trades to write to {out_path}")
        return
    df = pd.DataFrame(trades)
    if data is not None:
        stock_names = data.get("stock_names", {})
        industry = data.get("industry", {})

        def expand_codes(codes_str, mapper):
            if pd.isna(codes_str) or codes_str == "":
                return ""
            return ", ".join(f"{c}({mapper.get(c, '?')})" for c in codes_str.split("|"))

        def industries_of(codes_str):
            if pd.isna(codes_str) or codes_str == "":
                return ""
            return ", ".join(sorted(set(industry.get(c, "?") for c in codes_str.split("|"))))

        df["sells_labeled"] = df["sells"].apply(lambda s: expand_codes(s, stock_names))
        df["buys_labeled"] = df["buys"].apply(lambda s: expand_codes(s, stock_names))
        df["buys_industries"] = df["buys"].apply(industries_of)
        df["cum_nav_after"] = (1 + df["return_pct"].fillna(0) / 100).cumprod()
        df = df[
            [
                "selection_date",
                "rebalance_month",
                "n_held",
                "n_sold",
                "n_bought",
                "sells",
                "buys",
                "sells_labeled",
                "buys_labeled",
                "buys_industries",
                "return_pct",
                "traded_count",
                "cum_nav_after",
            ]
        ]
    df.to_csv(out_path, index=False)
    print(f"[out] trades: {out_path}  rows={len(df)}")


def equity_to_csv(eq, out_path):
    df = pd.DataFrame(
        {
            "date": eq.index.strftime("%Y-%m-%d"),
            "nav": eq.values,
            "monthly_return": eq.pct_change().fillna(0).values,
            "cum_return": (eq - 1.0).values,
            "peak_nav": eq.cummax().values,
        }
    )
    df["drawdown_pct"] = ((df["nav"] / df["peak_nav"] - 1) * 100).round(2)
    df["cum_log_return"] = np.log(df["nav"] / df["nav"].iloc[0])
    df = df[
        ["date", "nav", "monthly_return", "cum_return", "peak_nav", "drawdown_pct", "cum_log_return"]
    ]
    df.to_csv(out_path, index=False)
    print(f"[out] equity: {out_path}  rows={len(df)}")


# ==============================================================================
# Period / walk-forward helpers
# ==============================================================================


def split_index(pdf, start, end):
    sidx = int(pdf.index.searchsorted(pd.Timestamp(start), side="left"))
    eidx = int(pdf.index.searchsorted(pd.Timestamp(end), side="left"))
    return sidx, eidx


def run_period(data, score_fn, config, start, end):
    pdf = data["prices"]
    sidx, eidx = split_index(pdf, start, end)
    return run_backtest(
        data, score_fn, config, start_idx=max(0, sidx - config.warmup), end_idx=eidx
    )


def run_walkforward(
    data,
    score_fn,
    config,
    label,
    train_months=36,
    test_months=12,
    step_months=12,
):
    """Rolling walk-forward OOS validation (non-overlapping 12-month tests)."""
    all_dates = data["prices"].index
    n_total = len(all_dates)
    first_test_end = train_months + test_months
    if first_test_end > n_total:
        print(
            f"  [WARNING] Not enough data for walk-forward "
            f"(need {first_test_end} months, have {n_total})"
        )
        return []

    results = []
    last_test_start = n_total - test_months
    n_windows = 0
    t0 = time.time()

    for test_start_idx in range(train_months, last_test_start + 1, step_months):
        test_end_idx = min(test_start_idx + test_months, n_total)
        test_start = str(all_dates[test_start_idx].date())
        test_end = str(all_dates[test_end_idx - 1].date())

        r = run_period(data, score_fn, config, test_start, test_end)
        m = r.metrics

        results.append(
            {
                "window": len(results) + 1,
                "test_start": test_start,
                "test_end": test_end,
                "n_months": m["n_months"],
                "sharpe": round(m["sharpe"], 3),
                "nav": round(m["nav"], 4),
                "annual": round(m["annual"] * 100, 2),
                "max_dd": round(m["max_dd"] * 100, 1),
                "positive_months": f"{m['positive_months']}/{m['n_months']}",
            }
        )
        n_windows += 1

    elapsed = time.time() - t0
    sharpe_vals = [w["sharpe"] for w in results]
    pos_count = sum(1 for s in sharpe_vals if s > 0)
    best = max(sharpe_vals)
    worst = min(sharpe_vals)
    mean_sr = np.mean(sharpe_vals)

    print(f"\n=== Walk-Forward ({label}) ===")
    print(
        f"  Windows: {n_windows}  (train={train_months}m, test={test_months}m, step={step_months}m)"
    )
    print(f"  Time: {elapsed:.0f}s")
    for w in results:
        print(
            f"  window {w['window']:3d}  {w['test_start']}→{w['test_end']}  "
            f"Sharpe={w['sharpe']:+.3f}  NAV={w['nav']:.2f}  DD={w['max_dd']:.1f}%  "
            f"Ann={w['annual']:.1f}%"
        )
    print(f"\n  Walk-Forward OOS Sharpe distribution:")
    print(f"    Mean:  {mean_sr:+.3f}")
    print(f"    Best:  {best:+.3f}")
    print(f"    Worst: {worst:+.3f}  {'← negative' if worst < 0 else ''}")
    print(
        f"    % Positive: {pos_count}/{n_windows} ({100*pos_count/n_windows:.0f}%)"
    )
    print(
        f"    % Below 0.5: "
        f"{sum(1 for s in sharpe_vals if s < 0.5)}/{n_windows} "
        f"({100*sum(1 for s in sharpe_vals if s < 0.5)/n_windows:.0f}%)"
    )

    return {
        "config": {
            "train_months": train_months,
            "test_months": test_months,
            "step_months": step_months,
        },
        "n_windows": n_windows,
        "windows": results,
        "summary": {
            "mean_sharpe": round(float(mean_sr), 3),
            "best_sharpe": best,
            "worst_sharpe": worst,
            "pct_positive": round(pos_count / n_windows, 3),
            "pct_below_0_5": round(
                sum(1 for s in sharpe_vals if s < 0.5) / n_windows, 3
            ),
        },
    }


# ==============================================================================
# Main
# ==============================================================================


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--periods", action="store_true", help="Add sub-sample + IS/OOS analysis")
    p.add_argument(
        "--walkforward",
        action="store_true",
        help="Add rolling walk-forward OOS validation",
    )
    p.add_argument(
        "--no-tc",
        action="store_true",
        help="Disable transaction-cost modelling (overrides config.json default)",
    )
    p.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Override HDF5 path (also: $V21_DATA_H5 env var)",
    )
    p.add_argument(
        "--out-dir",
        type=str,
        default=str(RESULTS_DIR),
        help=f"Output directory (default: {RESULTS_DIR})",
    )
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True, parents=True)

    print("=" * 75)
    print(" V21 Production Backtest — alpha-engine-v21 skill")
    print(f" Run date: {datetime.now().isoformat()}")
    print("=" * 75)
    print(f"[config] {CONFIG_PATH}")
    print(f"[config] out dir: {out_dir}")

    cfg = load_v21_config(CONFIG_PATH, no_tc=args.no_tc)
    print(f"[config] {cfg.name}: n_hold={cfg.n_hold}  TC={cfg.transaction_cost}")

    data = load_v21_data(path=args.data_path)
    print(
        f"[data] prices={data['prices'].shape}, "
        f"mcap={data['market_cap'].shape}, "
        f"wt1={data['wt1_monthly'].shape}"
    )

    t0 = time.time()
    print(f"\n[run] V21 ({cfg.name}) ...")
    res = run_backtest(data, score_v21, cfg, start_idx=0)
    m = res.metrics
    print(
        f"  Sharpe={m['sharpe']:.3f}  NAV={m['nav']:.2f}  DD={m['max_dd']*100:.1f}%  "
        f"Ann={m['annual']*100:.1f}%  +{m['positive_months']}/{m['n_months']}  "
        f"cash={m['cash_months']}  turn={m['avg_turnover']:.2f}  "
        f"({time.time()-t0:.1f}s)"
    )

    out = {
        "config": {
            "name": cfg.name,
            "n_hold": cfg.n_hold,
            "max_per_ind": cfg.max_per_ind,
            "liq_filter_mcap": cfg.liq_filter_mcap,
            "ob_filter": cfg.ob_filter,
            "ob_base": cfg.ob_base,
            "ob_cap_adj": cfg.ob_cap_adj,
            "bad_return_threshold": cfg.bad_return_threshold,
            "warmup": cfg.warmup,
            "transaction_cost": cfg.transaction_cost,
        },
        "metrics": m,
        "equity_dates": [str(d) for d in res.equity.index],
        "equity_values": res.equity.values.tolist(),
        "trades": res.trades,
    }

    ret = pd.Series(
        out["equity_values"], index=pd.to_datetime(out["equity_dates"])
    ).pct_change().dropna()
    out["stats"] = honest_statistical_tests(ret, n_configs=5)
    s = out["stats"]
    print(
        f"  [stats] SR_ann={s['sharpe_annual']:.3f}  "
        f"p_iid={s['p_iid']:.4f}  p_nw={s['p_nw']:.4f}  "
        f"Boot CI=[{s['bootstrap_ci_95'][0]:.3f},{s['bootstrap_ci_95'][1]:.3f}]  "
        f"DSR={s['dsr']:.4f}"
    )

    if args.periods:
        periods = [
            ("2010-2014", "2010-01-01", "2015-01-01"),
            ("2015-2018", "2015-01-01", "2019-01-01"),
            ("2019-2021", "2019-01-01", "2022-01-01"),
            ("2022-2025", "2022-01-01", "2026-01-01"),
        ]
        print(f"\n[subsamples]")
        out["subsamples"] = {}
        out["is"] = None
        out["oos"] = None
        for n, s, e in periods:
            r = run_period(data, score_v21, cfg, s, e)
            out["subsamples"][n] = r.metrics
            print(f"  {n}:  Sharpe={r.metrics['sharpe']:+.3f}")

        r_is = run_period(data, score_v21, cfg, "2010-01-01", "2018-01-01")
        r_oos = run_period(data, score_v21, cfg, "2018-01-01", "2026-07-04")
        out["is"] = r_is.metrics
        out["oos"] = r_oos.metrics
        print(
            f"  IS={r_is.metrics['sharpe']:+.3f}  "
            f"OOS={r_oos.metrics['sharpe']:+.3f}"
        )

    if args.walkforward:
        print(f"\n--- Walk-Forward OOS Validation ---")
        out["walkforward"] = run_walkforward(
            data, score_v21, cfg, "V21", train_months=36, test_months=12, step_months=12
        )

    json_path = out_dir / "v21_authoritative_results.json"
    payload = {
        "engine": "alpha_engine.run_backtest",
        "run_date": datetime.now().isoformat(),
        "v21_release_notes": {
            "release":         "V21.0 (skill-port, 2026-07-19)",
            "strategy":        "V21 = lv(0.15) + wt_mom(0.85)",
            "tc_default":      "True (production honest default — overrides V21.0 research simplification)",
            "dsr_annualized":  True,
            "data_source":     "bundled V21 HDF5 (data/data_v20.h5)",
        },
        "results": out,
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\n[out] {json_path}")

    trades_to_csv(out["trades"], out_dir / "trades_v21.csv", data=data)
    equity_to_csv(
        pd.Series(out["equity_values"], index=pd.to_datetime(out["equity_dates"])).rename(
            "nav"
        ),
        out_dir / "equity_v21.csv",
    )

    print("\n" + "=" * 75)
    print(" V21 Release Summary")
    print("=" * 75)
    print(
        f" V21: Sharpe={m['sharpe']:.3f}  NAV={m['nav']:.2f}  "
        f"DD={m['max_dd']*100:.1f}%  Ann={m['annual']*100:.1f}%"
    )
    print("=" * 75)


if __name__ == "__main__":
    main()
