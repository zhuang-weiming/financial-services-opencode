#!/usr/bin/env python3
"""Factor analysis runner — IC/IR, quantile, correlation."""

import argparse
import json
from pathlib import Path

OUTPUT_DIR = Path("out")
OUTPUT_DIR.mkdir(exist_ok=True)


def run_icir(factor, universe, start_date, end_date):
    """Run IC/IR analysis for a factor."""
    try:
        from vibe_trading_quanta.factors.factor_analysis_core import FactorAnalysis
        fa = FactorAnalysis(
            factor_name=factor,
            universe=universe,
            start_date=start_date,
            end_date=end_date,
        )
        result = fa.compute_icir()
        return result
    except ImportError as e:
        return {"error": f"FactorAnalysis not available: {e}"}
    except Exception as e:
        return {"error": str(e)}


def run_quantile(factor, universe, n_groups=5):
    """Run quantile portfolio analysis."""
    try:
        from vibe_trading_quanta.factors.factor_analysis_core import FactorAnalysis
        fa = FactorAnalysis(factor_name=factor, universe=universe)
        result = fa.quantile_analysis(n_groups=n_groups)
        return result
    except ImportError as e:
        return {"error": f"FactorAnalysis not available: {e}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Factor analysis runner")
    parser.add_argument("action", choices=["icir", "quantile", "correlation"])
    parser.add_argument("--factor", required=True)
    parser.add_argument("--universe", default="csi300")
    parser.add_argument("--groups", type=int, default=5)
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.action == "icir":
        result = run_icir(args.factor, args.universe, args.start, args.end)
    elif args.action == "quantile":
        result = run_quantile(args.factor, args.universe, args.groups)
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
