#!/usr/bin/env python3
"""Market-aware data loader — detects market type and routes to correct loader.

Uses the vendored `vibe-trading-ai` tree (`backtest.loaders.registry`), which
carries the v0.1.15 market coverage (A-share / US / HK / Canada / India / Korea
KRX / Vietnam HOSE / UK LSE / crypto / futures / forex).
"""

import argparse
import json
import re
from pathlib import Path

OUTPUT_DIR = Path("out")
OUTPUT_DIR.mkdir(exist_ok=True)

# Our short market labels -> registry market keys (FALLBACK_CHAINS)
MARKET_KEY = {
    "a_share": "a_share",
    "us_equity": "us_equity",
    "hk_equity": "hk_equity",
    "crypto": "crypto",
    "forex": "forex",
    "india": "india_equity",
    "korea": "kr_equity",
    "vietnam": "vietnam_equity",
    "uk": "uk_equity",
    "canada": "ca_equity",
}


def detect_market(symbol):
    """Detect market from symbol pattern."""
    # A-share: 6-digit numeric
    if re.match(r'^\d{6}$', symbol) or re.match(r'^\d{6}\.(SZ|SH|BJ)$', symbol, re.I):
        return "a_share"
    # Crypto: BTC, ETH, etc.
    if re.match(r'^(BTC|ETH|XRP|USDT|DOGE|SOL|ADA|DOT|MATIC|AVAX|LINK|UNI|BNB|XMR)\b', symbol, re.I):
        return "crypto"
    # Korea: .KS / .KQ
    if symbol.endswith('.KS') or symbol.endswith('.KQ'):
        return "korea"
    # Vietnam: .VN
    if symbol.endswith('.VN'):
        return "vietnam"
    # UK: .L / .IL
    if symbol.endswith('.L') or symbol.endswith('.IL'):
        return "uk"
    # Canada: .TO / .V
    if symbol.endswith('.TO') or symbol.endswith('.V'):
        return "canada"
    # India: .NS / .BO suffix
    if symbol.endswith('.NS') or symbol.endswith('.BO'):
        return "india"
    # HK: 3-5 digit + .HK
    if re.match(r'^\d{3,5}\.HK$', symbol, re.I):
        return "hk_equity"
    # FX: 3+3 letters
    if re.match(r'^[A-Z]{3}[/\-]?[A-Z]{3}$', symbol, re.I):
        return "forex"
    # Default: US equity
    return "us_equity"


def load_data(symbol, market=None, start=None, end=None):
    """Load market data via the vendored vibe-trading-ai loader layer."""
    if not market:
        market = detect_market(symbol)

    try:
        from backtest.loaders.registry import resolve_loader

        market_key = MARKET_KEY.get(market, market)
        loader = resolve_loader(market_key)

        frames = loader.fetch([symbol], start_date=start, end_date=end)
        df = frames.get(symbol) if isinstance(frames, dict) else None

        if df is None or len(df) == 0:
            return {"market": market, "symbol": symbol, "error": "No data returned"}

        return {
            "market": market,
            "symbol": symbol,
            "loader": type(loader).__module__,
            "rows": len(df),
            "start": str(df.index.min()),
            "end": str(df.index.max()),
            "last_close": float(df["close"].iloc[-1]) if "close" in df.columns else None,
        }
    except Exception as e:
        return {"market": market, "symbol": symbol,
                "error": f"{type(e).__name__}: {e}"}


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
