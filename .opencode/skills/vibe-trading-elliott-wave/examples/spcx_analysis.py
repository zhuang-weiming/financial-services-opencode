"""
Elliott Wave Theory — generic analysis for ANY OHLCV DataFrame.

Automatically detects swing points via Zigzag and applies Elliott rules:
1. Wave 1 (first up-leg) / Wave 2 (retracement) validation
2. Iron rule check: Wave 2 cannot retrace beyond start of Wave 1
3. Sub-wave 5 Fibonacci projection targets

No hardcoded prices — works on any ticker's OHLCV.

Usage:
    from spcx_analysis import analyze_elliott
    result = analyze_elliott(df)   # df has [date, open, high, low, close, volume]

Signal: 5-wave advance complete → sell; ABC correction complete → buy.
"""
import sys
from pathlib import Path
import pandas as pd


def zigzag(df, threshold=0.05):
    """Identify swing highs/lows using rolling window with prominence threshold.

    Args:
        df: DataFrame with [date, high, low, ...]
        threshold: Minimum reversal magnitude as fraction (default 5%)

    Returns:
        List of (index, type, price) where type is 'H' or 'L'
    """
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)
    swings = []
    direction = 1  # start looking for high first
    cur_extreme_idx = 0
    cur_extreme_price = float(highs[0])

    for i in range(1, n):
        if direction >= 0:
            if highs[i] > cur_extreme_price:
                cur_extreme_idx = i; cur_extreme_price = float(highs[i])
            elif lows[i] < cur_extreme_price * (1 - threshold):
                swings.append((cur_extreme_idx, "H", cur_extreme_price))
                direction = -1
                cur_extreme_idx = i; cur_extreme_price = float(lows[i])
        if direction <= 0:
            if lows[i] < cur_extreme_price:
                cur_extreme_idx = i; cur_extreme_price = float(lows[i])
            elif highs[i] > cur_extreme_price * (1 + threshold):
                swings.append((cur_extreme_idx, "L", cur_extreme_price))
                direction = 1
                cur_extreme_idx = i; cur_extreme_price = float(highs[i])

    if direction >= 0:
        swings.append((cur_extreme_idx, "H", cur_extreme_price))
    else:
        swings.append((cur_extreme_idx, "L", cur_extreme_price))
    return swings


def find_impulse_legs(df, swings=None, threshold=0.08):
    """Find the dominant Wave 1 → Wave 2 pair from the DataFrame.

    Simple, robust, generic approach:
    - Wave 1 = from the FIRST data point (or first swing) to the overall high
    - Wave 2 = from the overall high to the overall LOW that follows it

    This captures the dominant impulse regardless of intra-wave noise.

    Returns dict or None if no valid structure.
    """
    if swings is None:
        swings = zigzag(df, threshold=threshold)
    if len(df) < 5:
        return None

    overall_high_idx = int(df["high"].idxmax())
    overall_high = float(df["high"].max())

    # Wave 1 origin: first swing point before the high, or first close
    prior = [s for s in swings if s[0] < overall_high_idx]
    if prior:
        # pick the extreme (low) before the high as origin
        origin_candidates = [s for s in prior if s[1] == "L"]
        if origin_candidates:
            origin_idx, _, origin = origin_candidates[-1]
        else:
            origin_idx, _, origin = prior[0]
    else:
        origin_idx = 0
        origin = float(df["open"].iloc[0])

    # Wave 2 low: overall low AFTER the high
    after = df["low"].iloc[overall_high_idx:]
    low_idx_local = int(after.idxmin())
    wave2_low = float(after.min())

    wave1_size = overall_high - origin
    wave2_size = overall_high - wave2_low
    if wave1_size <= 0:
        return None

    return {
        "origin": origin, "origin_idx": origin_idx,
        "wave1_high": overall_high, "wave1_high_idx": overall_high_idx,
        "wave2_low": wave2_low, "wave2_low_idx": low_idx_local,
        "wave1_size": wave1_size, "wave2_size": wave2_size,
        "retrace_pct": wave2_size / wave1_size,
        "invalid": wave2_size / wave1_size > 1.0,
        "direction": "up",
    }


def analyze_elliott(df):
    """Apply Elliott Wave rules to any OHLCV DataFrame.

    Auto-detects the most recent impulse Wave 1→Wave 2 pair, checks the
    iron rule, and projects sub-wave 5 targets from the last swing low.

    Returns: dict with all computed values.
    """
    major_swings = zigzag(df, threshold=0.08)
    swings_dated = [
        (df["date"].iloc[i].strftime("%Y-%m-%d"), t, round(p, 2), i)
        for i, t, p in major_swings
    ]

    last_close = float(df["close"].iloc[-1])

    # --- Primary wave structure (auto-detected) ---
    legs = find_impulse_legs(df, major_swings, threshold=0.08)

    if legs is None:
        # Fallback: use overall high/low as wave 1 / wave 2
        overall_high_idx = int(df["high"].idxmax())
        overall_high = float(df["high"].max())
        first_idx = 0
        first_price = float(df["open"].iloc[0])
        low_after = float(df["low"].iloc[overall_high_idx:].min())
        low_after_idx = int(df["low"].iloc[overall_high_idx:].idxmin())
        wave1_size = overall_high - first_price
        wave2_size = overall_high - low_after
        legs = {
            "origin": first_price, "origin_idx": first_idx,
            "wave1_high": overall_high, "wave1_high_idx": overall_high_idx,
            "wave2_low": low_after, "wave2_low_idx": low_after_idx,
            "wave1_size": wave1_size, "wave2_size": wave2_size,
            "retrace_pct": (wave2_size / wave1_size) if wave1_size > 0 else 0,
            "invalid": wave1_size > 0 and wave2_size / wave1_size > 1.0,
        }

    wave1_high = legs["wave1_high"]
    wave2_low = legs["wave2_low"]
    wave1_origin = legs["origin"]
    wave1_size = legs["wave1_size"]
    wave2_size = legs["wave2_size"]
    wave2_retr_pct = legs["retrace_pct"]
    wave2_invalid = legs["invalid"]

    # --- Sub-wave count from wave2_low (bullish leg) ---
    # Use major swings (8% threshold) with extreme-coalescing, which filters
    # the earnings-day micro-noise while preserving the clean H/L alternation.
    medium_swings = zigzag(df, threshold=0.08)
    after_raw = [(i, t, p) for i, t, p in medium_swings if i > legs["wave2_low_idx"]]

    after_low = []
    for i, t, p in after_raw:
        if not after_low:
            after_low.append((i, t, p))
            continue
        # Same type as last pivot → keep the more extreme value
        if t == after_low[-1][1]:
            if (t == "H" and p > after_low[-1][2]) or (t == "L" and p < after_low[-1][2]):
                after_low[-1] = (i, t, p)
            continue
        # Opposite type → check magnitude before recording a new pivot
        move = abs(p - after_low[-1][2]) / after_low[-1][2] if after_low[-1][2] else 0
        if move >= 0.05:
            after_low.append((i, t, p))
    sub_result = {}
    if len(after_low) >= 2:
        # sub-wave 1: wave2_low → first swing high after
        sw1_idx, sw1_t, sw1_price = after_low[0]
        sub_w1_high = sw1_price if sw1_t == "H" else None
        # find next swing low (sub-wave 2)
        sub_w2_low = None
        sub_w3_high = None
        sub_w4_low = None
        sw_points = [p for _, _, p in after_low]
        sw_types = [t for _, t, _ in after_low]
        if len(sw_points) >= 1:
            sub_w1_high = sw_points[0] if sw_types[0] == "H" else None
        if len(sw_points) >= 2:
            sub_w2_low = sw_points[1] if sw_types[1] == "L" else None
        if len(sw_points) >= 3:
            sub_w3_high = sw_points[2] if sw_types[2] == "H" else None
        if len(sw_points) >= 4:
            sub_w4_low = sw_points[3] if sw_types[3] == "L" else None
        if sub_w4_low is None and len(sw_points) >= 5:
            sub_w4_low = sw_points[4] if sw_types[4] == "L" else sub_w4_low

        if sub_w1_high and sub_w2_low and sub_w3_high and sub_w4_low:
            sub_w1_size = sub_w1_high - wave2_low
            sub_w2_retrace = (sub_w1_high - sub_w2_low) / sub_w1_size if sub_w1_size > 0 else 0
            sub_w3_size = sub_w3_high - sub_w2_low
            sub_w4_retrace = (sub_w3_high - sub_w4_low) / sub_w3_size if sub_w3_size > 0 else 0
            sub_result = {
                "sub_w1_high": sub_w1_high,
                "sub_w2_low": sub_w2_low,
                "sub_w3_high": sub_w3_high,
                "sub_w4_low": sub_w4_low,
                "sub_w1_size": sub_w1_size,
                "sub_w2_retrace_pct": sub_w2_retrace,
                "sub_w3_size": sub_w3_size,
                "sub_w4_retrace_pct": sub_w4_retrace,
                "sub_w5_target_eq_w1": sub_w4_low + sub_w1_size,
                "sub_w5_target_eq_0618_w3": sub_w4_low + sub_w3_size * 0.618,
                "sub_w5_target_eq_w3": sub_w4_low + sub_w3_size,
            }

    return {
        "wave1_origin": wave1_origin,
        "wave1_high": wave1_high,
        "wave2_low": wave2_low,
        "wave1_size": wave1_size,
        "wave2_size": wave2_size,
        "wave2_retr_pct": wave2_retr_pct,
        "wave2_invalid": wave2_invalid,
        "last_close": last_close,
        "swings": swings_dated,
        **sub_result,
    }


if __name__ == "__main__":
    # Demo on SPCX sample data (or any loaded DataFrame)
    import os
    demo_path = Path(__file__).parent.parent.parent / "_shared" / "sample_data.py"
    if demo_path.exists():
        sys.path.insert(0, str(demo_path.parent))
        from sample_data import load_spcx
        df = load_spcx()
    else:
        from data_loader import load_ohlcv
        df = load_ohlcv("AAPL")

    r = analyze_elliott(df)

    print("=" * 80)
    print(f"ELLIOTT WAVE ANALYSIS — {len(df)} rows, last close ${r['last_close']:.2f}")
    print("=" * 80)
    print(f"\nAuto-detected primary wave structure:")
    print(f"  Wave 1 origin:  ${r['wave1_origin']:.2f}")
    print(f"  Wave 1 high:    ${r['wave1_high']:.2f} (+${r['wave1_size']:.2f})")
    print(f"  Wave 2 low:     ${r['wave2_low']:.2f} (-${r['wave2_size']:.2f})")
    print(f"  Wave 2 retracement: {r['wave2_retr_pct']*100:.1f}% of Wave 1")
    if r["wave2_invalid"]:
        print(f"  🚨 WAVE 2 INVALID: retraced beyond 100% (Elliott iron rule violated)")
        print(f"  → Structural implication: larger bear cycle likely")

    if "sub_w1_high" in r:
        print(f"\nSub-wave count from ${r['wave2_low']:.2f} low (bullish leg):")
        print(f"  Sub-W1: ${r['wave2_low']:.2f} → ${r['sub_w1_high']:.2f} = +${r['sub_w1_size']:.2f}")
        print(f"  Sub-W2: ${r['sub_w1_high']:.2f} → ${r['sub_w2_low']:.2f} = {r['sub_w2_retrace_pct']*100:.1f}% retrace")
        print(f"  Sub-W3: ${r['sub_w2_low']:.2f} → ${r['sub_w3_high']:.2f} = +${r['sub_w3_size']:.2f}")
        print(f"  Sub-W4: ${r['sub_w3_high']:.2f} → ${r['sub_w4_low']:.2f} = {r['sub_w4_retrace_pct']*100:.1f}% retrace")
        print(f"\nSub-Wave 5 targets:")
        print(f"  Wave 1 equality:   ${r['sub_w5_target_eq_w1']:.2f}")
        print(f"  Wave 3 × 0.618:    ${r['sub_w5_target_eq_0618_w3']:.2f}")
        print(f"  Wave 3 equality:   ${r['sub_w5_target_eq_w3']:.2f}")
    else:
        print(f"\n(Insufficient swing data for sub-wave count)")
