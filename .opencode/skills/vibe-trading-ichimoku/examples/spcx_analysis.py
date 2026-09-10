"""
Ichimoku Kinko Hyo — example analysis on SPCX 55-day OHLCV.

NOTE: 55 days < 78 required for full warm-up. Senkou Span B is invalid;
Tenkan (9) and Kijun (26) are valid. Senkou Span A is computable but
forward-projected 26 bars.

Signal: Bullish TK cross + price above cloud + bullish cloud → strong buy.
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))
from sample_data import load_spcx


def ichimoku(df, tenkan=9, kijun=26, senkou_b=52, disp=26):
    """Compute Ichimoku Kinko Hyo five-line system.

    Returns: (tenkan_sen, kijun_sen, senkou_a, senkou_b, chikou_span)
    """
    h, l, c = df["high"], df["low"], df["close"]
    tenkan_sen = (h.rolling(tenkan).max() + l.rolling(tenkan).min()) / 2
    kijun_sen = (h.rolling(kijun).max() + l.rolling(kijun).min()) / 2
    senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(disp)
    senkou_b = ((h.rolling(senkou_b).max() + l.rolling(senkou_b).min()) / 2).shift(disp)
    chikou = c.shift(-disp)
    return tenkan_sen, kijun_sen, senkou_a, senkou_b, chikou


def analyze_ichimoku(df):
    """Compute Ichimoku and assess cloud position + TK crosses."""
    tenkan, kijun, sa, sb, chikou = ichimoku(df)
    last_close = df["close"].iloc[-1]
    last_date = df["date"].iloc[-1].strftime("%Y-%m-%d")
    n = len(df)

    tenk_v = float(tenkan.iloc[-1]) if pd.notna(tenkan.iloc[-1]) else None
    kij_v = float(kijun.iloc[-1]) if pd.notna(kijun.iloc[-1]) else None
    sa_v = float(sa.iloc[-1]) if pd.notna(sa.iloc[-1]) else None
    sb_v = float(sb.iloc[-1]) if pd.notna(sb.iloc[-1]) else None

    # Cloud position
    if sa_v is not None and sb_v is not None:
        cloud_top = max(sa_v, sb_v)
        cloud_bot = min(sa_v, sb_v)
        if last_close > cloud_top:
            cloud_pos = "above cloud (强势)"
        elif last_close < cloud_bot:
            cloud_pos = "below cloud (弱势)"
        else:
            cloud_pos = "inside cloud (中性)"
    else:
        cloud_pos = "indeterminate — Senkou Span B still warming up (need 78 bars)"
        cloud_top = cloud_bot = None

    # TK crossover detection
    crosses = []
    for i in range(1, n):
        if pd.notna(tenkan.iloc[i-1]) and pd.notna(tenkan.iloc[i]) and \
           pd.notna(kijun.iloc[i-1]) and pd.notna(kijun.iloc[i]):
            if tenkan.iloc[i-1] <= kijun.iloc[i-1] and tenkan.iloc[i] > kijun.iloc[i]:
                crosses.append((df["date"].iloc[i].strftime("%Y-%m-%d"), "bullish TK cross",
                              round(float(tenkan.iloc[i]), 2), round(float(kijun.iloc[i]), 2)))
            elif tenkan.iloc[i-1] >= kijun.iloc[i-1] and tenkan.iloc[i] < kijun.iloc[i]:
                crosses.append((df["date"].iloc[i].strftime("%Y-%m-%d"), "bearish TK cross",
                              round(float(tenkan.iloc[i]), 2), round(float(kijun.iloc[i]), 2)))

    return {
        "tenkan": tenk_v, "kijun": kij_v, "senkou_a": sa_v, "senkou_b": sb_v,
        "cloud_position": cloud_pos,
        "cloud_top": round(cloud_top, 2) if cloud_top else None,
        "cloud_bottom": round(cloud_bot, 2) if cloud_bot else None,
        "last_close": last_close, "last_date": last_date,
        "tk_crosses": crosses,
        "warmup_status": f"INCOMPLETE — only {n} of 78 required for Senkou Span B; Tenkan(9) and Kijun(26) are valid",
    }


if __name__ == "__main__":
    df = load_spcx()
    r = analyze_ichimoku(df)

    print("=" * 80)
    print(f"ICHIMOKU KINKO HYO — SPCX {len(df)} days")
    print("=" * 80)
    print(f"\nLatest values (as of {r['last_date']}):")
    print(f"  Tenkan-sen (9):   ${r['tenkan']:.2f}" if r['tenkan'] else "  Tenkan-sen: N/A")
    print(f"  Kijun-sen (26):   ${r['kijun']:.2f}" if r['kijun'] else "  Kijun-sen: N/A")
    print(f"  Senkou Span A:    ${r['senkou_a']:.2f}" if r['senkou_a'] else "  Senkou A:   N/A")
    print(f"  Senkou Span B:    {'$'+str(r['senkou_b'])+' [INCOMPLETE]' if r['senkou_b'] else 'N/A (insufficient data)'}")
    print(f"  Last close:       ${r['last_close']:.2f}")
    print(f"\nCloud position: {r['cloud_position']}")
    print(f"\nTK crossover history:")
    if r["tk_crosses"]:
        for d, sig, t, k in r["tk_crosses"]:
            print(f"  {d}: {sig} (Tenkan={t}, Kijun={k})")
    else:
        print("  (none)")
    print(f"\n{r['warmup_status']}")
