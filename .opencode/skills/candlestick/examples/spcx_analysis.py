"""
Candlestick Pattern Recognition — example analysis on SPCX 55-day OHLCV.

Implements 15 classic Japanese candlestick patterns with scoring:
- Single: Doji, Hammer, Inverted Hammer, Shooting Star, Spinning Top
- Double: Bullish/Bearish Engulfing, Harami, Piercing Line, Dark Cloud Cover
- Triple: Morning Star, Evening Star, Three White Soldiers, Three Black Crows

Signal logic: Bullish patterns score +1, bearish -1, neutral 0.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Load sample data
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))
from sample_data import load_spcx


def detect_candles(df, body_pct=0.10, shadow_ratio=2.0):
    """Score each daily candle with bullish (+1) / bearish (-1) / neutral (0).

    Args:
        df: DataFrame with columns [date, open, high, low, close, volume]
        body_pct: Threshold for body-to-range ratio in doji detection (default 0.10)
        shadow_ratio: Min ratio of shadow length to body length (default 2.0)

    Returns:
        List of (date_str, pattern_name, score) tuples
    """
    rng = df["high"] - df["low"]
    body = (df["close"] - df["open"]).abs()
    upper = df["high"] - df[["close", "open"]].max(axis=1)
    lower = df[["close", "open"]].min(axis=1) - df["low"]
    is_bull = df["close"] > df["open"]
    body_ratio = np.where(rng > 0, body / rng, 0)

    patterns = []
    for i in range(len(df)):
        r = rng.iloc[i]; bd = body.iloc[i]; u = upper.iloc[i]; l = lower.iloc[i]
        bull = is_bull.iloc[i]
        label = "—"; score = 0

        if r == 0:
            patterns.append((df["date"].iloc[i].strftime("%Y-%m-%d"), "Doji (zero-range)", 0))
            continue

        # Single-candle patterns
        if bd <= body_pct * r:                       # Doji family
            if u > shadow_ratio * bd and l > shadow_ratio * bd:
                label, score = "Long-legged Doji", 0
            elif u > shadow_ratio * bd:
                label, score = "Gravestone Doji", -1
            elif l > shadow_ratio * bd:
                label, score = "Dragonfly Doji", +1
            else:
                label, score = "Doji", 0
        elif l >= shadow_ratio * bd and u < bd * 0.5 and not bull:
            label, score = "Hammer", +1
        elif u >= shadow_ratio * bd and l < bd * 0.5 and not bull:
            label, score = "Inverted Hammer", +1
        elif u >= shadow_ratio * bd and l < bd * 0.5 and bull:
            label, score = "Shooting Star", -1
        elif l >= shadow_ratio * bd and u < bd * 0.5 and bull:
            label, score = "Hanging Man", -1
        elif bd < 0.4 * r and u > 0.6 * r and l > 0.6 * r:
            label, score = "Spinning Top", 0

        # Double-candle (uses yesterday context)
        if i > 0:
            prev_open = df["open"].iloc[i-1]; prev_close = df["close"].iloc[i-1]
            prev_bull = prev_close > prev_open
            if (not prev_bull) and bull and prev_open > df["close"].iloc[i] and prev_close < df["open"].iloc[i]:
                label, score = "Bullish Engulfing", +1
            elif prev_bull and (not bull) and prev_open < df["close"].iloc[i] and prev_close > df["open"].iloc[i]:
                label, score = "Bearish Engulfing", -1
            elif (not prev_bull) and bull and prev_open > df["open"].iloc[i] and prev_close < df["close"].iloc[i]:
                label, score = "Bullish Harami", +1
            elif prev_bull and (not bull) and prev_open < df["open"].iloc[i] and prev_close > df["close"].iloc[i]:
                label, score = "Bearish Harami", -1
            elif (not prev_bull) and bull and df["open"].iloc[i] < df["low"].iloc[i-1] and df["close"].iloc[i] > (prev_open + prev_close) / 2:
                label, score = "Piercing Line", +1
            elif prev_bull and (not bull) and df["open"].iloc[i] > df["high"].iloc[i-1] and df["close"].iloc[i] < (prev_open + prev_close) / 2:
                label, score = "Dark Cloud Cover", -1

        # Triple-candle patterns
        if i > 1 and bd > body_pct * r:
            d2_close = df["close"].iloc[i-2]; d1_close = df["close"].iloc[i-1]
            d2_red = d2_close < df["open"].iloc[i-2]
            d1_red = d1_close < df["open"].iloc[i-1]
            d1_green = d1_close > df["open"].iloc[i-1]
            rng_d1 = df["high"].iloc[i-1] - df["low"].iloc[i-1]
            body_d1 = abs(d1_close - df["open"].iloc[i-1])
            if d2_red and body_d1 <= body_pct * max(rng_d1, 1e-6) and bull and df["close"].iloc[i] > (df["open"].iloc[i-2] + d2_close) / 2:
                label, score = "Morning Star", +1
            elif (not d2_red) and body_d1 <= body_pct * max(rng_d1, 1e-6) and (not bull) and df["close"].iloc[i] < (df["open"].iloc[i-2] + d2_close) / 2:
                label, score = "Evening Star", -1
            elif (not d2_red) and d1_green and bull and d1_close > d2_close and df["close"].iloc[i] > d1_close:
                label, score = "Three White Soldiers", +1
            elif d2_red and d1_red and (not bull) and d1_close < d2_close and df["close"].iloc[i] < d1_close:
                label, score = "Three Black Crows", -1

        patterns.append((df["date"].iloc[i].strftime("%Y-%m-%d"), label, score))
    return patterns


if __name__ == "__main__":
    df = load_spcx()
    patterns = detect_candles(df)
    total_score = sum(p[2] for p in patterns)
    recent_score = sum(p[2] for p in patterns[-10:])

    print("=" * 80)
    print(f"CANDLESTICK ANALYSIS — SPCX {len(df)} days")
    print("=" * 80)
    print(f"\nLast 10 days:")
    print(f"{'Date':<12} {'Pattern':<25} {'Score':>6}")
    print("-" * 45)
    for d, p, s in patterns[-10:]:
        print(f"{d:<12} {p:<25} {s:>+6}")
    print(f"\nRecent 10-day score: {recent_score:+d} ({'Bullish' if recent_score > 0 else 'Bearish' if recent_score < 0 else 'Neutral'})")
    print(f"55-day aggregate score: {total_score:+d}")
    print(f"\nKey reversal patterns detected:")
    key_dates = {"2026-06-16": "52w HIGH $225.64 — top reversal",
                 "2026-07-28": "Post-3-crows low — bottom reversal",
                 "2026-08-26/27/28/31": "Three White Soldiers continuation"}
    for date, desc in key_dates.items():
        for d, p, s in patterns:
            if d in date.split("/") and s != 0:
                print(f"  {d}: {p} ({desc}) — score {s:+d}")
