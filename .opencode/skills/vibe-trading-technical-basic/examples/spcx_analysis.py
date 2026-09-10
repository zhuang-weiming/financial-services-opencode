"""
Technical Basic — example analysis on SPCX 55-day OHLCV.

Three-dimensional voting:
- Trend: EMA(12/26) + ADX(14)
- Mean Reversion: Bollinger Bands(20,2) + RSI(14)
- Volume-Price: OBV + Volume Ratio

Signal: Long = trend bullish + RSI not overbought + OBV rising; etc.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))
from sample_data import load_spcx


def ema(s, n):
    """Exponential moving average."""
    return s.ewm(span=n, adjust=False).mean()


def rsi_wilder(close, period=14):
    """RSI using Wilder's smoothing (EWM with alpha=1/period)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def adx_wilder(df, period=14):
    """ADX using Wilder's smoothing. Returns (ADX, +DI, -DI)."""
    h, l, c = df["high"], df["low"], df["close"]
    up = h.diff(); dn = -l.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx, plus_di, minus_di


def bb(close, n=20, k=2):
    """Bollinger Bands: (middle, upper, lower)."""
    ma = close.rolling(n).mean()
    sd = close.rolling(n).std(ddof=0)
    return ma, ma + k*sd, ma - k*sd


def analyze_tech_basic(df):
    """Compute all standard technical indicators."""
    ema12 = ema(df["close"], 12)
    ema26 = ema(df["close"], 26)
    adx, pdi, ndi = adx_wilder(df, 14)
    ma, bbu, bbl = bb(df["close"], 20, 2)
    rsi = rsi_wilder(df["close"], 14)
    obv = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
    vol_ma20 = df["volume"].rolling(20).mean()

    last_close = df["close"].iloc[-1]
    e12 = float(ema12.iloc[-1])
    e26 = float(ema26.iloc[-1])
    adx_v = float(adx.iloc[-1])
    pdi_v = float(pdi.iloc[-1])
    ndi_v = float(ndi.iloc[-1])
    ma_v = float(ma.iloc[-1])
    bbu_v = float(bbu.iloc[-1])
    bbl_v = float(bbl.iloc[-1])
    rsi_v = float(rsi.iloc[-1])
    obv_v = float(obv.iloc[-1])
    obv_5d_ago = float(obv.iloc[-6])
    vol_ratio = float(df["volume"].iloc[-1] / vol_ma20.iloc[-1])

    # Three-dimensional voting
    trend_signal = "bullish" if e12 > e26 else "bearish"
    trend_strength = "strong trend" if adx_v > 25 else "weak/no trend"
    rsi_status = ("overbought (>70)" if rsi_v > 70 else
                  ("oversold (<30)" if rsi_v < 30 else "neutral"))
    obv_trend = "rising" if obv_v > obv_5d_ago else "falling"

    return {
        "last_close": last_close,
        "EMA12": round(e12, 2), "EMA26": round(e26, 2),
        "EMA_cross": "bullish" if e12 > e26 else "bearish",
        "ADX": round(adx_v, 2), "+DI": round(pdi_v, 2), "-DI": round(ndi_v, 2),
        "trend": trend_signal, "trend_strength": trend_strength,
        "BB_mid": round(ma_v, 2), "BB_upper": round(bbu_v, 2),
        "BB_lower": round(bbl_v, 2), "BB_width_pct": round((bbu_v - bbl_v) / ma_v * 100, 2),
        "BB_position": ("above upper" if last_close > bbu_v else
                        ("below lower" if last_close < bbl_v else "inside")),
        "RSI": round(rsi_v, 2), "RSI_status": rsi_status,
        "OBV": round(obv_v, 0),
        "OBV_5d_change_pct": round((obv_v - obv_5d_ago) / abs(obv_5d_ago) * 100, 1),
        "OBV_trend": obv_trend,
        "Volume_ratio_today_vs_20dMA": round(vol_ratio, 2),
    }


if __name__ == "__main__":
    df = load_spcx()
    r = analyze_tech_basic(df)

    print("=" * 80)
    print(f"TECHNICAL BASIC — SPCX {len(df)} days")
    print("=" * 80)
    print(f"\nLast close: ${r['last_close']:.2f}")
    print(f"\nTrend dimension:")
    print(f"  EMA(12) = ${r['EMA12']:.2f}, EMA(26) = ${r['EMA26']:.2f} → {r['EMA_cross']}")
    print(f"  ADX(14) = {r['ADX']:.2f} ({r['trend_strength']})")
    print(f"  +DI = {r['+DI']:.2f}, -DI = {r['-DI']:.2f}")
    print(f"\nMean-reversion dimension:")
    print(f"  BB(20,2): mid=${r['BB_mid']:.2f}, upper=${r['BB_upper']:.2f}, lower=${r['BB_lower']:.2f}")
    print(f"  Width: {r['BB_width_pct']}% (high vol regime)" if r['BB_width_pct'] > 20 else f"  Width: {r['BB_width_pct']}%")
    print(f"  Position: {r['BB_position']}")
    print(f"  RSI(14) = {r['RSI']:.2f} ({r['RSI_status']})")
    print(f"\nVolume-price dimension:")
    print(f"  OBV: {r['OBV']:,.0f}")
    print(f"  OBV 5d change: {r['OBV_5d_change_pct']:+.1f}% ({r['OBV_trend']})")
    print(f"  Today volume / 20d MA: {r['Volume_ratio_today_vs_20dMA']:.2f}")

    # Three-dimensional voting
    votes = []
    votes.append(("Trend", r["EMA_cross"]))
    votes.append(("Mean-Rev", r["RSI_status"]))
    votes.append(("Vol-Price", "bullish" if r["OBV_trend"] == "rising" else "bearish"))
    print(f"\nThree-dimensional vote: {dict(votes)}")
    bull_count = sum(1 for _, v in votes if "bullish" in v)
    print(f"  Net: {bull_count}/3 bullish → {'Mildly Bullish' if bull_count >= 2 else 'Mildly Bearish'}")
