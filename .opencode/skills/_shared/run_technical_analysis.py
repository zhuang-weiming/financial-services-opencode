#!/usr/bin/env python3
"""
Unified Technical Analysis Entry Point — analyze ANY ticker with 8 frameworks.

This is the reusable, generic entry point for the 8 trend-analysis skills
(candlestick / elliott-wave / ichimoku / harmonic / technical-basic /
chanlun / smc / gann). It loads any symbol's OHLCV and runs all 8 frameworks.

Usage:
    python3 .opencode/skills/_shared/run_technical_analysis.py AAPL
    python3 .opencode/skills/_shared/run_technical_analysis.py 600519
    python3 .opencode/skills/_shared/run_technical_analysis.py BTC-USD
    python3 .opencode/skills/_shared/run_technical_analysis.py AAPL --limit 250
    python3 .opencode/skills/_shared/run_technical_analysis.py 600519 --market cn
    python3 .opencode/skills/_shared/run_technical_analysis.py data.csv
    python3 .opencode/skills/_shared/run_technical_analysis.py AAPL --skills elliott,gann
    python3 .opencode/skills/_shared/run_technical_analysis.py AAPL --json out.json

All algorithms are REAL implementations (pandas/numpy/math), no mocks.
Data source priority: llmquant-data MCP → yfinance → akshare → tushare → mootdx.
"""
import argparse
import json
import sys
from pathlib import Path

SHARED = Path(__file__).parent
sys.path.insert(0, str(SHARED))
sys.path.insert(0, str(SHARED.parent / "candlestick" / "examples"))
sys.path.insert(0, str(SHARED.parent / "elliott-wave" / "examples"))
sys.path.insert(0, str(SHARED.parent / "ichimoku" / "examples"))
sys.path.insert(0, str(SHARED.parent / "harmonic" / "examples"))
sys.path.insert(0, str(SHARED.parent / "technical-basic" / "examples"))
sys.path.insert(0, str(SHARED.parent / "chanlun" / "examples"))
sys.path.insert(0, str(SHARED.parent / "smc" / "examples"))
sys.path.insert(0, str(SHARED.parent / "gann" / "examples"))

from data_loader import load_ohlcv, infer_market


def load_skill_function(skill_name, func_name):
    """Import a function from a skill example module."""
    import importlib
    mod = importlib.import_module(f"spcx_analysis")
    # each example defines analyze_<skill>
    return getattr(mod, func_name)


def run_all(df, symbol, skills_to_run=None):
    """Run all requested frameworks and collect structured output."""
    results = {"symbol": symbol, "rows": len(df),
               "date_start": str(df["date"].iloc[0].date()),
               "date_end": str(df["date"].iloc[-1].date()),
               "last_close": float(df["close"].iloc[-1])}
    skill_map = {
        "candlestick": ("detect_candles", "candlestick"),
        "elliott": ("analyze_elliott", "elliott-wave"),
        "ichimoku": ("analyze_ichimoku", "ichimoku"),
        "harmonic": ("analyze_harmonic", "harmonic"),
        "technical-basic": ("analyze_tech_basic", "technical-basic"),
        "chanlun": ("analyze_chanlun", "chanlun"),
        "smc": ("analyze_smc", "smc"),
        "gann": ("analyze_gann", "gann"),
    }
    # Import each module by adding its examples dir and importing
    for key, (func, skill_dir) in skill_map.items():
        if skills_to_run and key not in skills_to_run:
            continue
        try:
            mod_path = SHARED.parent / skill_dir / "examples" / "spcx_analysis.py"
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                f"skill_{skill_dir}", mod_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if key == "candlestick":
                patterns = mod.detect_candles(df)
                total = sum(p[2] for p in patterns)
                recent = sum(p[2] for p in patterns[-10:])
                results[key] = {"recent_10d_score": recent,
                                "total_score": total,
                                "last_10": [(d, p, s) for d, p, s in patterns[-10:]]}
            else:
                fn = getattr(mod, func)
                r = fn(df)
                results[key] = r
        except Exception as e:
            results[key] = {"error": str(e)}
    return results


def main():
    parser = argparse.ArgumentParser(description="8-framework technical analysis for any ticker")
    parser.add_argument("symbol", help="Ticker (AAPL / 600519 / BTC-USD) or CSV path")
    parser.add_argument("--market", default="auto", help="auto|us|cn|hk|crypto")
    parser.add_argument("--limit", type=int, default=500, help="max rows")
    parser.add_argument("--period", default="1y", help="yfinance period (us/crypto)")
    parser.add_argument("--skills", default=None, help="comma list: candlestick,elliott,ichimoku,harmonic,technical-basic,chanlun,smc,gann")
    parser.add_argument("--json", default=None, help="save structured JSON output to path")
    parser.add_argument("--no-print", action="store_true", help="don't print per-framework summary")
    args = parser.parse_args()

    skills = args.skills.split(",") if args.skills else None

    print(f"=== Loading {args.symbol} (market={args.market}, limit={args.limit}) ===")
    df = load_ohlcv(args.symbol, market=args.market, period=args.period, limit=args.limit)
    print(f"  Loaded {len(df)} rows: {df['date'].iloc[0].date()} → {df['date'].iloc[-1].date()}")
    print(f"  Last close: ${df['close'].iloc[-1]:.2f}")

    results = run_all(df, args.symbol, skills)

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2, default=str))
        print(f"\nJSON saved to {args.json}")

    if not args.no_print:
        print("\n" + "=" * 70)
        print(f"TECHNICAL ANALYSIS SUMMARY — {args.symbol}")
        print("=" * 70)

        if "candlestick" in results:
            c = results["candlestick"]
            n_days = results.get("rows", 0)
            print(f"\n[1] CANDLESTICK")
            print(f"    {n_days}d aggregate: {c.get('total_score')}, recent 10d: {c.get('recent_10d_score')}")

        if "elliott" in results:
            e = results["elliott"]
            print(f"\n[2] ELLIOTT WAVE")
            print(f"    Wave2 retrace: {e.get('wave2_retr_pct', 'N/A')}")
            print(f"    Wave2 invalid: {e.get('wave2_invalid', 'N/A')}")
            if e.get("sub_w5_target_eq_w1"):
                print(f"    Sub-W5 targets: ${e['sub_w5_target_eq_w1']:.2f} / ${e.get('sub_w5_target_eq_0618_w3', 0):.2f} / ${e.get('sub_w5_target_eq_w3', 0):.2f}")

        if "ichimoku" in results:
            i = results["ichimoku"]
            print(f"\n[3] ICHIMOKU")
            print(f"    Tenkan: {i.get('tenkan')}, Kijun: {i.get('kijun')}")
            print(f"    Cloud: {i.get('cloud_position')}")

        if "harmonic" in results:
            h = results["harmonic"]
            print(f"\n[4] HARMONIC")
            print(f"    Matches: {len(h.get('matches', []))}")

        if "technical-basic" in results:
            t = results["technical-basic"]
            print(f"\n[5] TECHNICAL BASIC")
            print(f"    EMA12/26: {t.get('EMA12')}/{t.get('EMA26')}, ADX: {t.get('ADX')}")
            print(f"    RSI: {t.get('RSI')}, OBV 5d: {t.get('OBV_5d_change_pct')}%")

        if "chanlun" in results:
            ch = results["chanlun"]
            print(f"\n[6] CHANLUN")
            print(f"    Fractals: {len(ch.get('fractals', []))}, Strokes: {len(ch.get('strokes', []))}, ZS: {len(ch.get('central_zones', []))}")

        if "smc" in results:
            s = results["smc"]
            print(f"\n[7] SMC")
            print(f"    Structure: {s.get('structure')}")

        if "gann" in results:
            g = results["gann"]
            print(f"\n[8] GANN")
            print(f"    50% midpoint: {g.get('50pct_midpoint')}, distance: {g.get('distance_to_50pct_pct')}%")
            print(f"    Rule of 7: {g.get('rule_of_7', {}).get('interpretation', 'N/A')}")

        print("\n" + "=" * 70)
        print("All 8 frameworks are REAL pandas/numpy/math implementations.")
        print("Data source: llmquant-data MCP → yfinance → akshare → tushare → mootdx.")
        print("This is research only — NOT a trade instruction.")
        print("=" * 70)


if __name__ == "__main__":
    main()
