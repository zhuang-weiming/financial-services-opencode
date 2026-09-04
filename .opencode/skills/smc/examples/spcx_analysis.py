"""
Smart Money Concepts (ICT) — example analysis on SPCX 55-day OHLCV.

⚠️ **Note**: The `smartmoneyconcepts` PyPI library works but expects
specific DataFrame formats. This pure-Python implementation provides
the core SMC logic (BOS/ChoCH/FVG/OB) with explicit control.

Concepts:
- BOS (Break of Structure): trend continuation
- ChoCH (Change of Character): trend reversal
- FVG (Fair Value Gap): 3-candle imbalance
- OB (Order Block): last opposite candle before strong move

Signal: bullish ChoCH + BOS + FVG → long; bearish analog → short.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))
from sample_data import load_spcx


def smc_analysis(df, swing_window=5):
    """Pure-Python SMC analysis.

    Args:
        df: DataFrame with [date, open, high, low, close, volume]
        swing_window: bars on each side for swing detection

    Returns: dict with structure direction, BOS, ChoCH, OB, FVG
    """
    h = df["high"].values; l = df["low"].values
    c = df["close"].values; o = df["open"].values
    n = len(df)

    # Swing detection
    swing_highs = []; swing_lows = []
    for i in range(swing_window, n - swing_window):
        if h[i] == max(h[i-swing_window:i+swing_window+1]):
            swing_highs.append((i, float(h[i])))
        if l[i] == min(l[i-swing_window:i+swing_window+1]):
            swing_lows.append((i, float(l[i])))

    # BOS / ChoCH detection
    bos_events = []; choch_events = []
    prev_sh = swing_highs[0] if swing_highs else None
    prev_sl = swing_lows[0] if swing_lows else None
    last_structure = "neutral"

    for i in range(1, n):
        if prev_sh and c[i] > prev_sh[1] and o[i] > prev_sh[1]:
            if last_structure == "bearish":
                evt = ("ChoCH↑", i, prev_sh[1])
                choch_events.append(evt); last_structure = "bullish"
            else:
                bos_events.append(("BOS↑", i, prev_sh[1])); last_structure = "bullish"
            future_sh = [x for x in swing_highs if x[0] > i]
            prev_sh = future_sh[0] if future_sh else prev_sh
        if prev_sl and c[i] < prev_sl[1] and o[i] < prev_sl[1]:
            if last_structure == "bullish":
                evt = ("ChoCH↓", i, prev_sl[1])
                choch_events.append(evt); last_structure = "bearish"
            else:
                bos_events.append(("BOS↓", i, prev_sl[1])); last_structure = "bearish"
            future_sl = [x for x in swing_lows if x[0] > i]
            prev_sl = future_sl[0] if future_sl else prev_sl

    # Order Blocks: last opposite-direction candle before BOS/ChoCH
    obs = []
    for typ, idx, lvl in bos_events + choch_events:
        if "↑" in typ:
            for k in range(idx-1, max(0, idx-6), -1):
                if c[k] < o[k]:
                    obs.append({"type": "bullish OB",
                                "date": df["date"].iloc[k].strftime("%Y-%m-%d"),
                                "high": round(float(h[k]), 2),
                                "low": round(float(l[k]), 2)})
                    break
        else:
            for k in range(idx-1, max(0, idx-6), -1):
                if c[k] > o[k]:
                    obs.append({"type": "bearish OB",
                                "date": df["date"].iloc[k].strftime("%Y-%m-%d"),
                                "high": round(float(h[k]), 2),
                                "low": round(float(l[k]), 2)})
                    break

    # FVG: 3-candle pattern with gap
    fvgs = []
    for i in range(1, n-1):
        if l[i+1] > h[i-1]:  # bullish FVG
            fvgs.append({"type": "bullish FVG",
                         "start": df["date"].iloc[i-1].strftime("%Y-%m-%d"),
                         "end": df["date"].iloc[i+1].strftime("%Y-%m-%d"),
                         "high": round(float(h[i-1]), 2),
                         "low": round(float(l[i+1]), 2)})
        elif h[i+1] < l[i-1]:  # bearish FVG
            fvgs.append({"type": "bearish FVG",
                         "start": df["date"].iloc[i-1].strftime("%Y-%m-%d"),
                         "end": df["date"].iloc[i+1].strftime("%Y-%m-%d"),
                         "high": round(float(h[i+1]), 2),
                         "low": round(float(l[i-1]), 2)})

    return {
        "structure": last_structure,
        "swing_highs": swing_highs,
        "swing_lows": swing_lows,
        "bos_events": bos_events,
        "choch_events": choch_events,
        "order_blocks": obs[-5:],
        "fvgs": fvgs[-5:],
    }


def analyze_smc(df):
    """Run SMC analysis with dated events."""
    r = smc_analysis(df, swing_window=5)

    bos_dated = [
        {"event": typ, "date": df["date"].iloc[idx].strftime("%Y-%m-%d"), "level": round(lvl, 2)}
        for typ, idx, lvl in r["bos_events"][-10:]
    ]
    choch_dated = [
        {"event": typ, "date": df["date"].iloc[idx].strftime("%Y-%m-%d"), "level": round(lvl, 2)}
        for typ, idx, lvl in r["choch_events"]
    ]

    # Date the recent OB/FVG
    for ob in r["order_blocks"]:
        # already dated in smc_analysis
        pass

    return {
        "structure": r["structure"],
        "bos": bos_dated,
        "choch": choch_dated,
        "order_blocks": r["order_blocks"],
        "fvgs": r["fvgs"],
        "swing_high_count": len(r["swing_highs"]),
        "swing_low_count": len(r["swing_lows"]),
    }


if __name__ == "__main__":
    df = load_spcx()
    r = analyze_smc(df)

    print("=" * 80)
    print(f"SMART MONEY CONCEPTS (ICT) — SPCX {len(df)} days")
    print("=" * 80)
    print(f"\nCurrent structure: {r['structure'].upper()}")
    print(f"Detected {r['swing_high_count']} swing highs, {r['swing_low_count']} swing lows")

    print(f"\nBOS events (last 10):")
    for b in r["bos"]:
        print(f"  {b['date']}: {b['event']} @ ${b['level']:.2f}")

    print(f"\nChoCH events (reversals):")
    for c in r["choch"]:
        print(f"  {c['date']}: {c['event']} @ ${c['level']:.2f}")

    print(f"\nOrder Blocks (recent 5):")
    for ob in r["order_blocks"]:
        print(f"  {ob['type']}: {ob['date']}, range ${ob['low']:.2f}-${ob['high']:.2f}")

    print(f"\nFair Value Gaps (recent 5):")
    for fvg in r["fvgs"]:
        print(f"  {fvg['type']}: {fvg['start']} → {fvg['end']}, "
              f"range ${fvg['low']:.2f}-${fvg['high']:.2f}")
