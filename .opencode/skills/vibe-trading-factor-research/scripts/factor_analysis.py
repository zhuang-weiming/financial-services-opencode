#!/usr/bin/env python3
"""Factor analysis runner — IC/IR, quantile, correlation.

Uses the vendored `vibe-trading-ai` Quant Library
(`src.factors.factor_analysis_core`) which exposes functional IC/quantile
primitives:

    compute_ic_series(factor_df, return_df) -> pd.Series
    compute_group_equity(...)               -> pd.DataFrame

The pre-0.1.15 class-based `FactorAnalysis(factor_name, universe, ...)` API no
longer exists, so this runner now takes explicit factor/return panels. To bench
a *zoo* family end-to-end, use the `vibe-trading-alpha-zoo` runner instead
(`run_bench(zoo=..., universe=..., period=...)`).
"""

import argparse
import json
from pathlib import Path

OUTPUT_DIR = Path("out")
OUTPUT_DIR.mkdir(exist_ok=True)


def _load_csv(path):
    import pandas as pd
    df = pd.read_csv(path)
    # Accept either a date column or a date index.
    for col in ("date", "trade_date", "datetime"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
            df = df.set_index(col)
            break
    return df


def run_icir(factor_csv, return_csv, method="pearson"):
    """Compute the IC series + summary stats from factor and return panels."""
    try:
        from src.factors.factor_analysis_core import compute_ic_series

        factor_df = _load_csv(factor_csv)
        return_df = _load_csv(return_csv)
        ic = compute_ic_series(factor_df, return_df)

        ic = ic.dropna()
        n = int(len(ic))
        if n == 0:
            return {"error": "no overlapping factor/return observations after dropna"}

        import numpy as np
        mean = float(ic.mean())
        std = float(ic.std())
        return {
            "n_observations": n,
            "ic_mean": round(mean, 4),
            "ic_std": round(std, 4),
            "icir": round(mean / std, 4) if std > 0 else None,
            "ic_positive_ratio": round(float((ic > 0).mean()), 4),
            "ic_t_stat": round(mean / std * np.sqrt(n), 3) if std > 0 else None,
        }
    except ImportError as e:
        return {"error": f"src.factors.factor_analysis_core not available: {e}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def run_quantile(factor_csv, return_csv, n_groups=5):
    """Compute quantile-group equity curves from factor and return panels."""
    try:
        from src.factors.factor_analysis_core import compute_group_equity

        factor_df = _load_csv(factor_csv)
        return_df = _load_csv(return_csv)
        equity = compute_group_equity(factor_df, return_df, n_groups=n_groups)
        return {
            "n_groups": n_groups,
            "rows": int(len(equity)) if hasattr(equity, "__len__") else None,
            "columns": list(equity.columns) if hasattr(equity, "columns") else None,
            "tail": equity.tail(3).to_dict() if hasattr(equity, "tail") else None,
        }
    except ImportError as e:
        return {"error": f"src.factors.factor_analysis_core not available: {e}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def main():
    parser = argparse.ArgumentParser(description="Factor analysis runner")
    parser.add_argument("action", choices=["icir", "quantile", "correlation"])
    parser.add_argument("--factor-csv", help="Factor panel CSV (date + one column per asset)")
    parser.add_argument("--return-csv", help="Return panel CSV (same shape as factor)")
    parser.add_argument("--factor", default=None,
                        help="Zoo factor id (informational; use vibe-trading-alpha-zoo for bench)")
    parser.add_argument("--universe", default="csi300")
    parser.add_argument("--groups", type=int, default=5)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.action in ("icir", "quantile") and not (args.factor_csv and args.return_csv):
        result = {
            "error": "This runner needs --factor-csv and --return-csv panels "
                     "(the class-based FactorAnalysis(factor_name, universe, ...) API "
                     "was removed in v0.1.15). To bench a zoo family, use the "
                     "vibe-trading-alpha-zoo runner's `run_bench`."
        }
    elif args.action == "icir":
        result = run_icir(args.factor_csv, args.return_csv)
    elif args.action == "quantile":
        result = run_quantile(args.factor_csv, args.return_csv, args.groups)
    elif args.action == "correlation":
        result = {"message": "Correlation analysis not yet wired"}
    else:
        result = {"error": "Unknown action"}

    output = json.dumps(result, indent=2, default=str)
    if args.output:
        path = OUTPUT_DIR / args.output
        path.write_text(output)
        print(f"Written to {path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
