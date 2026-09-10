#!/usr/bin/env python3
"""Backtest runner — delegates to the vendored Vibe-Trading CLI (``backtest.runner``).

The vendored ``backtest/*`` tree is installed editable at
``.opencode/python/vibe-trading/`` (pyproject name ``vibe-trading-ai``), so
the canonical entrypoint ``python -m backtest.runner <run_dir>`` is importable
globally. This wrapper builds a valid run directory (config.json +
code/signal_engine.py), then invokes that CLI.

Usage:
    python backtest_runner.py run --engine daily --source a_share --symbol 600519.SH \
        --start 2023-01-01 --end 2025-12-31 --capital 100000
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SIGNAL_TEMPLATE = '''"""Signal engine for CLI-driven backtest."""
import numpy as np
import pandas as pd


class SignalEngine:
    """Momentum-on-close signal engine (sign of 20-day close change).

    ``generate`` receives a symbol -> OHLCV DataFrame map and returns a
    symbol -> signal Series map (1=long, -1=short, 0=flat).
    """

    def generate(self, data_map):
        result = {}
        for symbol, df in data_map.items():
            close = df["close"].astype(float)
            result[symbol] = np.sign(close.pct_change(20).fillna(0.0))
        return result
'''


def _allowed_root() -> Path:
    """Pick the first writable allowed run root from the vendored guard."""
    from src.tools.path_utils import _allowed_run_roots  # noqa: PLC2701

    for root in _allowed_run_roots():
        r = Path(root)
        try:
            r.mkdir(parents=True, exist_ok=True)
            return r
        except OSError:
            continue
    return Path(".").resolve()


def run_backtest(engine, source, symbols, start, end, initial_capital=100000):
    """Run a backtest via the canonical `python -m backtest.runner` CLI."""
    try:
        import backtest.runner  # noqa: F401  (verify the vendored tree is importable)
    except ImportError as e:
        return {"error": f"Vendored Vibe-Trading not importable: {e}"}

    root = _allowed_root()
    run_dir = Path(tempfile.mkdtemp(prefix="bt-run-", dir=root))
    (run_dir / "code").mkdir(parents=True)
    (run_dir / "code" / "signal_engine.py").write_text(SIGNAL_TEMPLATE)
    config = {
        "codes": symbols,
        "start_date": start,
        "end_date": end,
        "source": source or "auto",
        "interval": "1D",
        "engine": engine,
        "initial_cash": initial_capital,
    }
    (run_dir / "config.json").write_text(json.dumps(config, indent=2))

    proc = subprocess.run(
        [sys.executable, "-m", "backtest.runner", str(run_dir)],
        capture_output=True,
        text=True,
    )
    result = json.loads(proc.stdout) if proc.stdout.strip() else {}
    if proc.returncode != 0 and not result:
        result = {"error": proc.stderr.strip() or f"exit {proc.returncode}"}
    result["run_dir"] = str(run_dir)
    return result


def main():
    parser = argparse.ArgumentParser(description="Backtest runner (delegates to backtest.runner)")
    parser.add_argument("action", choices=["run"])
    parser.add_argument("--engine", default="daily")
    parser.add_argument("--source", default=None)
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--capital", type=float, default=100000)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    symbols = args.symbols.split(",") if args.symbols else (args.symbol or [])
    if not symbols:
        symbols = ["000300.SH"]

    result = run_backtest(args.engine, args.source, symbols, args.start, args.end, args.capital)
    output = json.dumps(result, indent=2, default=str)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()