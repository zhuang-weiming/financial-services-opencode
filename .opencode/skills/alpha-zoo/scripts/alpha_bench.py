#!/usr/bin/env python3
"""Alpha bench runner — wraps vibe_trading_quanta alpha zoo."""

import argparse
import sys
import json
from pathlib import Path

OUTPUT_DIR = Path("out")
OUTPUT_DIR.mkdir(exist_ok=True)


def list_families():
    """List available alpha families."""
    try:
        import vibe_trading_quanta.factors.zoo as zoo
        families = []
        for attr in dir(zoo):
            if not attr.startswith("_") and not attr == "zoo":
                try:
                    pkg = getattr(zoo, attr)
                    if hasattr(pkg, "__path__"):
                        families.append(attr)
                except Exception:
                    pass
        return families
    except ImportError as e:
        return [{"error": f"vibe_trading_quanta not available: {e}"}]


def run_bench(family, universe=None, top_n=10):
    """Run an alpha bench for a given family."""
    try:
        from vibe_trading_quanta.factors.bench_runner import AlphaBenchRunner
        runner = AlphaBenchRunner(family=family, universe=universe or "csi300")
        results = runner.run(top_n=top_n)
        return results
    except ImportError as e:
        return [{"error": f"BenchRunner not available: {e}"}]
    except Exception as e:
        return [{"error": str(e)}]


def main():
    parser = argparse.ArgumentParser(description="Alpha bench runner")
    parser.add_argument("action", choices=["list", "bench", "compare"])
    parser.add_argument("--family", default=None)
    parser.add_argument("--universe", default="csi300")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.action == "list":
        result = list_families()
    elif args.action == "bench":
        if not args.family:
            print("Error: --family required for bench action", file=sys.stderr)
            sys.exit(1)
        result = run_bench(args.family, args.universe, args.top)
    elif args.action == "compare":
        result = {"message": "Alpha compare not yet wired to vibe-trading-quanta"}
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
