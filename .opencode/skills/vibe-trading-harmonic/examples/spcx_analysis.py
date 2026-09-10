"""
Harmonic Patterns — generic analysis for ANY OHLCV DataFrame.

Detects XABCD 5-point structures (Gartley / Bat / Butterfly / Crab) using
Fibonacci geometry. No hardcoded prices — works on any ticker.

Patterns (B-point retracement, D-point retracement of XA):
    Gartley:   B = 0.618 XA,  D = 0.786 XA
    Bat:       B = 0.382-0.5 XA, D = 0.886 XA
    Butterfly: B = 0.786 XA,  D = 1.27 XA
    Crab:      B = 0.382-0.618 XA, D = 1.618 XA

Usage:
    from spcx_analysis import analyze_harmonic
    result = analyze_harmonic(df)

Signal: Bullish pattern (D at bottom) → buy; Bearish (D at top) → sell.
"""
import sys
from pathlib import Path
import pandas as pd


def zigzag(df, threshold=0.05):
    """Identify swing highs/lows using rolling window with prominence threshold."""
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)
    swings = []
    direction = 1
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


def find_xabcd(swings_list, tolerance=0.12):
    """Search for XABCD 5-point structures in swing points.

    Returns:
        List of dicts: {pattern, X, A, B, C, D, AB_XA, BC_AB, AD_XA, dates}
    """
    s = swings_list
    patterns_found = []
    for i in range(len(s) - 4):
        X, A, B, C, D = s[i], s[i+1], s[i+2], s[i+3], s[i+4]
        x_price, a_price, b_price = X[2], A[2], B[2]
        c_price, d_price = C[2], D[2]
        XA = abs(a_price - x_price)
        AB = abs(b_price - a_price)
        AD = abs(d_price - a_price)
        if XA == 0 or AB == 0:
            continue
        AB_XA = AB / XA
        AD_XA = AD / XA

        # Determine if this is a bullish (D below X) or bearish (D above X) setup
        bullish = a_price < x_price  # A is below X → downward leg first

        for name, b_lo, b_hi, d_target in [
            ("Gartley", 0.55, 0.65, 0.786),
            ("Bat", 0.382, 0.50, 0.886),
            ("Butterfly", 0.70, 0.85, 1.27),
            ("Crab", 0.382, 0.618, 1.618),
        ]:
            if b_lo - tolerance <= AB_XA <= b_hi + tolerance and \
               abs(AD_XA - d_target) <= tolerance * d_target:
                patterns_found.append({
                    "pattern": ("Bullish " if bullish else "Bearish ") + name,
                    "X": round(x_price, 2), "A": round(a_price, 2),
                    "B": round(b_price, 2), "C": round(c_price, 2),
                    "D": round(d_price, 2),
                    "X_date": X[0], "D_date": D[0],
                    "AB_XA": round(AB_XA, 3),
                    "AD_XA": round(AD_XA, 3),
                })
    return patterns_found


def analyze_harmonic(df, threshold=0.05):
    """Find harmonic patterns in any OHLCV DataFrame.

    Returns: dict with matches, recent swing structure, D target for the
    most likely forming pattern (based on the last 5 swings).
    """
    swings = zigzag(df, threshold=threshold)
    # Annotate dates
    swings_dated = [
        (df["date"].iloc[i].strftime("%Y-%m-%d"), t, p, i)
        for i, t, p in swings
    ]
    matches = find_xabcd(swings_dated, tolerance=0.12)

    last_close = float(df["close"].iloc[-1])

    # Analyze the last 5 swings for a "forming" pattern
    forming = None
    if len(swings_dated) >= 5:
        tail = swings_dated[-5:]
        X, A, B, C, D = tail
        x_price, a_price, b_price = X[2], A[2], B[2]
        c_price, d_price = C[2], D[2]
        XA = abs(a_price - x_price)
        if XA > 0:
            AB_XA = abs(b_price - a_price) / XA
            AD_XA = abs(d_price - a_price) / XA
            # For a bullish bat forming: AB/XA ~0.382-0.5, need D ~0.886 XA below A
            # For a bearish bat forming: AB/XA ~0.382-0.5, need D ~0.886 XA above A
            if abs(AB_XA - 0.44) <= 0.12:  # close to Bat B zone
                bullish = a_price < x_price
                if bullish:
                    d_needed = x_price - 0.886 * XA
                else:
                    d_needed = a_price + 0.886 * XA
                forming = {
                    "pattern": ("Bullish Bat" if bullish else "Bearish Bat") + " (forming)",
                    "X": round(x_price, 2), "A": round(a_price, 2),
                    "B": round(b_price, 2), "C": round(c_price, 2),
                    "D": round(d_price, 2),
                    "AB_XA": round(AB_XA, 3),
                    "AD_XA": round(AD_XA, 3),
                    "D_needed_for_completion": round(d_needed, 2),
                    "distance_to_D_pct": round((d_needed / d_price - 1) * 100, 1) if d_price else None,
                }

    return {
        "matches": matches,
        "forming_pattern": forming,
        "last_close": last_close,
        "swing_count": len(swings_dated),
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

    r = analyze_harmonic(df)

    print("=" * 80)
    print(f"HARMONIC PATTERNS — {len(df)} rows, last close ${r['last_close']:.2f}")
    print("=" * 80)
    print(f"\nDetected {r['swing_count']} swings")
    print(f"\nAutomated XABCD scan (12% tolerance):")
    if r["matches"]:
        for m in r["matches"]:
            print(f"  {m['pattern']}: X={m['X']} A={m['A']} B={m['B']} C={m['C']} D={m['D']}")
            print(f"    {m['X_date']} → {m['D_date']}, AB/XA={m['AB_XA']:.3f}, AD/XA={m['AD_XA']:.3f}")
    else:
        print("  No completed patterns found")

    if r["forming_pattern"]:
        f = r["forming_pattern"]
        print(f"\nForming pattern: {f['pattern']}")
        print(f"  X={f['X']} A={f['A']} B={f['B']} C={f['C']} D={f['D']}")
        print(f"  AB/XA={f['AB_XA']:.3f}, AD/XA={f['AD_XA']:.3f}")
        print(f"  D needed for completion: ${f['D_needed_for_completion']:.2f} "
              f"({f['distance_to_D_pct']:+.1f}% from current D)")
    else:
        print(f"\nNo forming Bat/Gartley structure in last 5 swings")
