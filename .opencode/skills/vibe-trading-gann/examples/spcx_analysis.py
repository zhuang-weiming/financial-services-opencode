"""
Gann Analysis — generic for ANY OHLCV DataFrame.

W.D. Gann's methods, computed automatically from the data:
1. **Gann Angles**: Time-price geometric ratios (1×1 = 45°, 2×1 = steeper)
2. **Square of 9**: Price levels derived from √price increments
3. **Time-Price Squaring**: Key calendar windows
4. **Rule of 7**: Market cycles at multiples of 7
5. **50% Rule**: Critical midpoint of price range

No hardcoded prices — works on any ticker. Uses the DataFrame's own
start date / overall high / overall low as reference points.

Usage:
    from spcx_analysis import analyze_gann
    result = analyze_gann(df)
"""
import sys
from pathlib import Path
import math
import pandas as pd


def gann_angles(start_price, start_date, current_date):
    """Calculate Gann angle lines (1×1, 1×2, 2×1) from a start point.

    1×1 = price rises $1 per day (45°)
    1×2 = price rises $0.5 per day (gentler)
    2×1 = price rises $2 per day (steeper)
    """
    days = max((current_date - start_date).days, 1)
    return {
        "days": days,
        "start_price": round(start_price, 2),
        "1x1": round(start_price + days * 1.0, 2),
        "1x2": round(start_price + days * 0.5, 2),
        "2x1": round(start_price + days * 2.0, 2),
    }


def square9(price):
    """Square of 9: each 45° adds 0.5 to √price.

    Returns dict of {angle: target_price} for 45°/90°/180°/270°/360°.
    """
    sqrt_p = math.sqrt(price)
    return {
        "45°": round((sqrt_p + 0.5) ** 2, 2),
        "90°": round((sqrt_p + 1.0) ** 2, 2),
        "180°": round((sqrt_p + 2.0) ** 2, 2),
        "270°": round((sqrt_p + 3.0) ** 2, 2),
        "360°": round((sqrt_p + 4.0) ** 2, 2),
    }


def rule_of_7(start_date, end_date):
    """Compute Rule of 7 alignment for a price swing."""
    days = max((end_date - start_date).days, 1)
    mod = days % 7
    if mod == 0:
        interp = f"{days} days = {days // 7} weeks exactly. Strong natural cycle alignment."
    else:
        interp = f"{days} days = {days // 7} weeks + {mod} days. Partial cycle alignment."
    return {"days": days, "mod7": mod, "interpretation": interp}


def midpoint_50pct(low, high):
    """50% Rule midpoint of price range."""
    return round(low + (high - low) * 0.5, 2)


def analyze_gann(df):
    """Comprehensive Gann analysis for any OHLCV DataFrame.

    Reference points are auto-derived:
    - Start: first trading day's open
    - Overall high: max(high) in window
    - Overall low: min(low) in window
    - Recent low: last swing low (via 5-bar rolling min)

    Returns: dict with all computed values.
    """
    start_date = df["date"].iloc[0]
    last_date = df["date"].iloc[-1]
    last_close = float(df["close"].iloc[-1])

    # Overall high/low
    hi = float(df["high"].max())
    lo = float(df["low"].min())
    hi_idx = int(df["high"].idxmax())
    lo_idx = int(df["low"].idxmin())

    # Recent low: last 5-bar minimum as "bounce origin"
    window = min(20, len(df))
    recent_slice = df.tail(window)
    recent_low = float(recent_slice["low"].min())
    recent_low_idx = int(recent_slice["low"].idxmin())
    recent_low_date = df["date"].iloc[recent_low_idx]

    # Start price: first close (more stable than first open)
    start_price = float(df["close"].iloc[0])

    # 1. Gann Angles from start
    angles_start = gann_angles(start_price, start_date, last_date)

    # 2. Gann Angles from recent low
    angles_recent_low = gann_angles(recent_low, recent_low_date, last_date)

    # 3. Square of 9 from current / overall high / overall low
    sq9_current = square9(last_close)
    sq9_hi = square9(hi)
    sq9_lo = square9(lo)

    # 4. Time-Price Squaring windows from start
    key_windows = [30, 45, 60, 90, 120, 180, 270, 360]
    time_windows = []
    days_since_start = (last_date - start_date).days
    for w in key_windows:
        target_date = start_date + pd.Timedelta(days=w)
        status = "passed" if last_date >= target_date else f"in {w - days_since_start} days"
        time_windows.append({"window_days": w,
                             "target_date": target_date.strftime("%Y-%m-%d"),
                             "status": status})

    # 5. Rule of 7 for recent-low → last-date swing
    r7 = rule_of_7(recent_low_date, last_date)

    # 6. 50% Rule midpoint
    mid_50 = midpoint_50pct(lo, hi)
    distance_pct = round((last_close - mid_50) / mid_50 * 100, 2) if mid_50 else 0

    # 7. Time-price squaring: recent low date as origin
    days_since_recent_low = (last_date - recent_low_date).days

    return {
        "last_close": last_close,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "last_date": last_date.strftime("%Y-%m-%d"),
        "overall_high": round(hi, 2),
        "overall_low": round(lo, 2),
        "recent_low": round(recent_low, 2),
        "recent_low_date": recent_low_date.strftime("%Y-%m-%d"),
        "start_price": round(start_price, 2),
        "angles_from_start": angles_start,
        "angles_from_recent_low": angles_recent_low,
        "sq9_current": sq9_current,
        "sq9_overall_high": sq9_hi,
        "sq9_overall_low": sq9_lo,
        "time_windows": time_windows,
        "rule_of_7": r7,
        "50pct_midpoint": mid_50,
        "distance_to_50pct_pct": distance_pct,
        "days_since_recent_low": days_since_recent_low,
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

    r = analyze_gann(df)

    print("=" * 80)
    print(f"GANN ANALYSIS — {len(df)} rows, {r['start_date']} → {r['last_date']}")
    print(f"Last close: ${r['last_close']:.2f}")
    print(f"Window: high ${r['overall_high']:.2f}, low ${r['overall_low']:.2f}, "
          f"recent low ${r['recent_low']:.2f} ({r['recent_low_date']})")
    print("=" * 80)

    print(f"\n1. Gann Angles from start (${r['start_price']:.2f}, {r['start_date']}):")
    a = r["angles_from_start"]
    print(f"   Days: {a['days']}")
    print(f"   1×1 (45°):  ${a['1x1']:.2f}  (current is {(r['last_close']/a['1x1']-1)*100:+.1f}%)")
    print(f"   1×2 (22.5°): ${a['1x2']:.2f}")

    print(f"\n2. Gann Angles from recent low (${r['recent_low']:.2f}, {r['recent_low_date']}):")
    a = r["angles_from_recent_low"]
    print(f"   Days: {a['days']}")
    print(f"   1×1: ${a['1x1']:.2f}  (current is {(r['last_close']/a['1x1']-1)*100:+.1f}%)")
    print(f"   2×1: ${a['2x1']:.2f}")

    print(f"\n3. Square of 9 from current ${r['last_close']:.2f}:")
    for deg, target in r["sq9_current"].items():
        print(f"   {deg}: ${target:.2f} ({(target/r['last_close']-1)*100:+.1f}%)")

    print(f"\n4. Time-Price Squaring from start:")
    for tw in r["time_windows"]:
        marker = "📍" if "in " in tw["status"] else "  "
        print(f"   {marker} {tw['window_days']}d: {tw['target_date']} ({tw['status']})")

    print(f"\n5. Rule of 7 ({r['recent_low_date']} → {r['last_date']}):")
    r7 = r["rule_of_7"]
    print(f"   {r7['interpretation']}")

    print(f"\n6. 50% Rule midpoint:")
    print(f"   Range: ${r['overall_low']:.2f} → ${r['overall_high']:.2f}")
    print(f"   50% midpoint: ${r['50pct_midpoint']:.2f}")
    print(f"   Current distance: {r['distance_to_50pct_pct']:+.1f}%")
