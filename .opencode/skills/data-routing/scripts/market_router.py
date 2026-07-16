#!/usr/bin/env python3
"""Market-aware data loader — detects market type and routes to correct loader."""

import argparse
import json
import re
from pathlib import Path

OUTPUT_DIR = Path("out")
OUTPUT_DIR.mkdir(exist_ok=True)


def detect_market(symbol):
    """Detect market from symbol pattern."""
    # A-share: 6-digit numeric
    if re.match(r'^\d{6}$', symbol) or re.match(r'^\d{6}\.(SZ|SH)$', symbol, re.I):
        return "a_share"
    # Crypto: BTC, ETH, etc.
    if re.match(r'^(BTC|ETH|XRP|USDT|DOGE|SOL|ADA|DOT|MATIC|AVAX|LINK|UNI|BNB|XMR)\b', symbol, re.I):
        return "crypto"
    # FX: 3+3 letters
    if re.match(r'^[A-Z]{3}[A-Z]{3}$', symbol, re.I):
        return "forex"
    # India: .NS or .BO suffix
    if symbol.endswith('.NS') or symbol.endswith('.BO'):
        return "india"
    # Default: US equity
    return "us_equity"


def load_data(symbol, market=None, start=None, end=None):
    """Load market data via vibe-trading-quanta loaders."""
    if not market:
        market = detect_market(symbol)

    try:
        from vibe_trading_quanta.loaders.base import DataLoader

        loader_routes = {
            "a_share": "vibe_trading_quanta.loaders.mootdx_loader",
            "us_equity": "vibe_trading_quanta.loaders.yfinance_loader",
            "crypto": "vibe_trading_quanta.loaders.okx",
            "forex": "vibe_trading_quanta.loaders.yfinance_loader",
            "india": "vibe_trading_quanta.loaders.yfinance_loader",
        }

        import importlib
        mod_path = loader_routes.get(market)
        if not mod_path:
            return {"error": f"No loader for market: {market}"}

        mod = importlib.import_module(mod_path)
        loader = getattr(mod, "loader", None) or DataLoader()

        result = loader.fetch(
            symbol=symbol,
            start_date=start,
            end_date=end,
        )
        return {
            "market": market,
            "symbol": symbol,
            "data": result if result else {"error": "No data returned"},
        }
    except ImportError as e:
        return {"market": market, "symbol": symbol, "error": f"Loader import error: {e}"}
    except Exception as e:
        return {"market": market, "symbol": symbol, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Market data router")
    parser.add_argument("action", choices=["detect", "load"])
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--market", default=None)
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.action == "detect":
        result = {"symbol": args.symbol, "detected_market": detect_market(args.symbol)}
    elif args.action == "load":
        result = load_data(args.symbol, args.market, args.start, args.end)
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
