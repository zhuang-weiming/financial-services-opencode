#!/usr/bin/env python3
"""Alpha bench runner — wraps the vendored vibe-trading-ai alpha zoo.

Uses `src.factors.zoo` (462 alphas across qlib158 / alpha101 / gtja191 /
academic / fundamental) and `src.factors.bench_runner.run_bench` from the
vendored `vibe-trading-ai` tree (v0.1.15).
"""

import argparse
import sys
import json
from pathlib import Path

OUTPUT_DIR = Path("out")
OUTPUT_DIR.mkdir(exist_ok=True)


def list_families():
    """List available alpha families (zoo subpackages on disk)."""
    try:
        import os
        import src.factors.zoo as zoo
        zoo_dir = os.path.dirname(zoo.__file__)
        families = [
            name for name in os.listdir(zoo_dir)
            if os.path.isdir(os.path.join(zoo_dir, name))
            and not name.startswith(("_", "."))
        ]
        return sorted(families)
    except ImportError as e:
        return [{"error": f"src.factors.zoo not available: {e}"}]


def run_bench_action(family, universe=None, top_n=10, period="2020-2024"):
    """Run an alpha bench for a given zoo family."""
    try:
        from src.factors.bench_runner import run_bench
        return run_bench(
            zoo=family,
            universe=universe or "csi300",
            period=period,
            top=top_n,
        )
    except ImportError as e:
        return {"error": f"src.factors.bench_runner not available: {e}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def main():
    parser = argparse.ArgumentParser(description="Alpha bench runner")
    parser.add_argument("action", choices=["list", "bench", "compare"])
    parser.add_argument("--family", default=None)
    parser.add_argument("--universe", default="csi300")
    parser.add_argument("--period", default="2020-2024")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.action == "list":
        result = list_families()
    elif args.action == "bench":
        if not args.family:
            print("Error: --family required for bench action", file=sys.stderr)
            sys.exit(1)
        result = run_bench_action(args.family, args.universe, args.top, args.period)
    elif args.action == "compare":
        result = {"message": "Alpha compare not yet wired to the vendored engine"}
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
