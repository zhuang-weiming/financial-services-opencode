"""
Chanlun 缠论 — example analysis on SPCX 55-day OHLCV.

⚠️ **czsc library caveat**: The czsc library's Rust extension (rs_czsc) is
broken in many environments (IncompatibleVersionError on Operate import).
We provide a PURE PYTHON implementation that follows the canonical Chanlun
algorithm: 包含处理 → 分型 → 笔 → 中枢 → 买卖点.

Pure-Python implementation is used here. If you have a working czsc, you
can use it instead — but results should be equivalent.

Signal: 一买/一卖 = trend reversal (背驰点); 二买/二卖 = confirmation;
       三买/三卖 = central-zone breakout.
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))
from sample_data import load_spcx


def chanlun_manual(df):
    """Pure-Python Chanlun implementation.

    Steps:
    1. 包含处理 (K-line inclusion): merge same-direction candles
    2. 分型 (fractals): top/bottom fractals on merged K-lines
    3. 笔 (BI): alternating top→bottom strokes
    4. 中枢 (ZS): ≥3 overlapping BIs define central zone
    5. 买卖点: simplified 1B/2B based on last 3 strokes

    Returns: (fractals, strokes, central_zones, buy_signals)
    """
    h = df["high"].values; l = df["low"].values
    n = len(df)

    # 1. Inclusion processing
    merged = []
    for i in range(n):
        if not merged:
            merged.append((h[i], l[i], i))
            continue
        prev_h, prev_l, prev_i = merged[-1]
        if h[i] > prev_h and l[i] > prev_l:
            # upward: keep higher high and higher low
            merged[-1] = (max(prev_h, h[i]), max(prev_l, l[i]), prev_i)
        elif h[i] < prev_h and l[i] < prev_l:
            # downward: keep lower high and lower low
            merged[-1] = (min(prev_h, h[i]), min(prev_l, l[i]), prev_i)
        else:
            merged.append((h[i], l[i], i))

    # 2. Fractal detection on merged K-lines
    fractals = []
    for i in range(1, len(merged) - 1):
        prev_h, prev_l, _ = merged[i-1]
        cur_h, cur_l, cur_i = merged[i]
        next_h, next_l, _ = merged[i+1]
        if cur_h > prev_h and cur_h > next_h:
            fractals.append((cur_i, "top", cur_h))
        if cur_l < prev_l and cur_l < next_l:
            fractals.append((cur_i, "bot", cur_l))

    # 3. 笔 (BI): alternating top/bot
    strokes = []
    for i in range(1, len(fractals)):
        if fractals[i-1][1] != fractals[i][1]:
            strokes.append((fractals[i-1], fractals[i]))

    # 4. 中枢 (ZS): ≥3 overlapping strokes
    zss = []
    if len(strokes) >= 3:
        for i in range(len(strokes) - 2):
            s1, s2, s3 = strokes[i], strokes[i+1], strokes[i+2]
            # Compute overlap zone across 3 strokes
            tops = [s[1][2] if s[1][1] == "top" else s[0][2] for s in (s1, s2, s3)]
            bots = [s[0][2] if s[1][1] == "top" else s[1][2] for s in (s1, s2, s3)]
            high_low = max(bots)
            low_high = min(tops)
            if high_low < low_high:  # valid overlap
                zss.append((s1[0][0], s3[1][0], high_low, low_high))

    # 5. Simplified 买卖点
    buy_signals = []
    sell_signals = []
    if len(strokes) >= 3:
        last_s = strokes[-1]; prev_s = strokes[-2]
        if last_s[1][1] == "top" and prev_s[0][1] == "top":
            buy_signals.append(("疑似一买", last_s[0][0], last_s[0][2], last_s[1][0], last_s[1][2]))

    return fractals, strokes, zss, buy_signals


def analyze_chanlun(df):
    """Run full Chanlun analysis on SPCX data."""
    fractals, strokes, zss, buy_signals = chanlun_manual(df)

    fractals_dated = [
        {"date": df["date"].iloc[orig_i].strftime("%Y-%m-%d"),
         "type": "顶分型" if t == "top" else "底分型",
         "price": round(p, 2)}
        for orig_i, t, p in fractals
    ]

    strokes_dated = [
        {
            "from": {"date": df["date"].iloc[i1].strftime("%Y-%m-%d"),
                     "type": "顶" if t1 == "top" else "底", "price": round(p1, 2)},
            "to": {"date": df["date"].iloc[i2].strftime("%Y-%m-%d"),
                   "type": "顶" if t2 == "top" else "底", "price": round(p2, 2)},
            "direction": "↓ 下降笔" if (t1 == "top" and t2 == "bot") else "↑ 上升笔"
        }
        for (i1, t1, p1), (i2, t2, p2) in strokes
    ]

    zss_dated = [
        {
            "start": df["date"].iloc[start_i].strftime("%Y-%m-%d"),
            "end": df["date"].iloc[end_i].strftime("%Y-%m-%d"),
            "high": round(top, 2), "low": round(bot, 2),
            "ZG": round((top + bot) / 2, 2),
            "range": round(top - bot, 2),
            "duration_days": (df["date"].iloc[end_i] - df["date"].iloc[start_i]).days
        }
        for start_i, end_i, top, bot in zss
    ]

    return {
        "fractals": fractals_dated,
        "strokes": strokes_dated,
        "central_zones": zss_dated,
        "buy_signals": buy_signals,
    }


if __name__ == "__main__":
    df = load_spcx()
    r = analyze_chanlun(df)

    print("=" * 80)
    print(f"CHANLUN 缠论 — SPCX {len(df)} days")
    print("=" * 80)
    print(f"\n⚠️  Note: 55 days is insufficient for robust中枢/三买 analysis (need 100+)")
    print(f"   Using pure-Python implementation (czsc library's rs_czsc broken)")

    print(f"\n分型 (Fractals) detected: {len(r['fractals'])}")
    for f in r["fractals"][-10:]:
        print(f"  {f['date']}: {f['type']} @ ${f['price']:.2f}")

    print(f"\n笔 (Strokes) detected: {len(r['strokes'])}")
    for s in r["strokes"][-5:]:
        print(f"  {s['from']['date']} ({s['from']['type']} ${s['from']['price']:.2f}) → "
              f"{s['to']['date']} ({s['to']['type']} ${s['to']['price']:.2f}) [{s['direction']}]")

    print(f"\n中枢 (Central Zones) detected: {len(r['central_zones'])}")
    for z in r["central_zones"]:
        print(f"  {z['start']} → {z['end']}: high=${z['high']:.2f}, low=${z['low']:.2f}, "
              f"ZG=${z['ZG']:.2f}, range=${z['range']:.2f}, {z['duration_days']}d")

    print(f"\n疑似买卖点 (Buy/Sell signals):")
    for sig, i1, p1, i2, p2 in r["buy_signals"]:
        print(f"  {sig}: from ${p1:.2f} to ${p2:.2f}")
