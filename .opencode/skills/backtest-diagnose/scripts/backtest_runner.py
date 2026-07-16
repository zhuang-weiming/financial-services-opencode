#!/usr/bin/env python3
"""Backtest runner — wraps vibe_trading_quanta backtest engines."""

import argparse
import json
from pathlib import Path

OUTPUT_DIR = Path("out")
OUTPUT_DIR.mkdir(exist_ok=True)


ENGINE_MAP = {
    "china_a": "vibe_trading_quanta.backtest.engines.china_a",
    "global_equity": "vibe_trading_quanta.backtest.engines.global_equity",
    "crypto": "vibe_trading_quanta.backtest.engines.crypto",
    "forex": "vibe_trading_quanta.backtest.engines.forex",
    "composite": "vibe_trading_quanta.backtest.engines.composite",
    "options": "vibe_trading_quanta.backtest.engines.options_portfolio",
    "india": "vibe_trading_quanta.backtest.engines.india_equity",
    "china_futures": "vibe_trading_quanta.backtest.engines.china_futures",
    "global_futures": "vibe_trading_quanta.backtest.engines.global_futures",
}


def list_engines():
    return list(ENGINE_MAP.keys())


def run_backtest(engine, symbol, start, end, initial_capital=100000):
    """Run a backtest using the specified engine."""
    try:
        import importlib
        mod_path = ENGINE_MAP.get(engine)
        if not mod_path:
            return {"error": f"Unknown engine: {engine}. Available: {list_engines()}"}
        mod = importlib.import_module(mod_path)
        engine_cls = getattr(mod, "BacktestEngine", None)
        if not engine_cls:
            return {"error": f"No BacktestEngine class in {mod_path}"}
        bt = engine_cls()
        result = bt.run(
            symbols=[symbol],
            start_date=start,
            end_date=end,
            initial_capital=initial_capital,
        )
        return result
    except ImportError as e:
        return {"error": f"Import error: {e}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Backtest runner")
    parser.add_argument("action", choices=["list", "run"])
    parser.add_argument("--engine", default="china_a")
    parser.add_argument("--symbol", default="000300")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--capital", type=float, default=100000)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.action == "list":
        result = {"engines": list_engines()}
    elif args.action == "run":
        result = run_backtest(args.engine, args.symbol, args.start, args.end, args.capital)
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
