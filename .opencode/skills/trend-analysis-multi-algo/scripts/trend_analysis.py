#!/usr/bin/env python3
"""
trend_analysis.py — 多算法趋势分析统一执行器 (trend-analysis-multi-algo skill)

一次运行启动 9 种趋势算法：
  A. 动量层  : A1 WaveTrend(V21)  A2 技术三维投票(EMA/ADX+BB/RSI+OBV)
  B. 形态层  : B1 蜡烛图(TA-Lib)  B2 缠论(czsc)  B3 艾略特波浪  B4 谐波  B5 图表形态(MCP)
  C. 结构层  : C1 SMC/ICT  C2 一目均衡表  C3 江恩理论(Gann)
  D. 汇总裁决: 信号矩阵 + 分歧分析 + 时间尺度分层 + 独立性质检

用法:
    python3 trend_analysis.py --code 601788 --market sh --bars 640
    python3 trend_analysis.py --csv /path/prices.csv        # 需含 date,open,high,low,close,volume
    python3 trend_analysis.py --code 601788 --json-out out.json

依赖: pandas numpy talib czsc smartmoneyconcepts (可选 pyharmonics)
数据源: 腾讯行情(默认, 无鉴权) → 失败回退 akshare/mootdx
"""
from __future__ import annotations
import argparse
import json
import sys
import warnings
from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------------
# 数据获取
# ----------------------------------------------------------------------------

def fetch_tencent(code: str, market: str, start: str, end: str) -> pd.DataFrame:
    """腾讯行情日线 (qfq 前复权)。code 例: 601788, market: sh/sz。"""
    import requests
    sym = f"{market}{code}"
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {"param": f"{sym},day,{start},{end},2000,qfq"}
    r = requests.get(url, params=params, timeout=30,
                     headers={"User-Agent": "Mozilla/5.0"})
    d = r.json()["data"][sym]
    key = "qfqday" if "qfqday" in d else "day"
    rows = d[key]
    df = pd.DataFrame([x[:6] for x in rows],
                      columns=["date", "open", "close", "high", "low", "volume"])
    for c in ["open", "close", "high", "low", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    return df.reset_index(drop=True)


def fetch_akshare(code: str, start: str, end: str) -> pd.DataFrame:
    import akshare as ak
    df = ak.stock_zh_a_hist(symbol=code, period="daily",
                            start_date=start.replace("-", ""),
                            end_date=end.replace("-", ""), adjust="qfq")
    df = df.rename(columns={"日期": "date", "开盘": "open", "收盘": "close",
                            "最高": "high", "最低": "low", "成交量": "volume"})
    df["date"] = pd.to_datetime(df["date"])
    return df[["date", "open", "close", "high", "low", "volume"]].reset_index(drop=True)


def load_data(args) -> pd.DataFrame:
    if args.csv:
        df = pd.read_csv(args.csv)
        df.columns = [c.lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"])
        return df.reset_index(drop=True)
    end = args.end
    start = args.start
    try:
        df = fetch_tencent(args.code, args.market, start, end)
        if len(df) > 0:
            return df
    except Exception as e:
        print(f"[warn] tencent failed: {e}", file=sys.stderr)
    try:
        return fetch_akshare(args.code, start, end)
    except Exception as e:
        print(f"[warn] akshare failed: {e}", file=sys.stderr)
    raise RuntimeError("no data source available")


# ----------------------------------------------------------------------------
# 结果容器
# ----------------------------------------------------------------------------

@dataclass
class AlgoResult:
    name: str
    layer: str            # momentum / pattern / structure
    scale: str            # long / mid / short
    direction: int        # -1 bear, 0 neutral, +1 bull
    strength: float       # 0..1
    readings: dict = field(default_factory=dict)
    note: str = ""
    ok: bool = True


# ----------------------------------------------------------------------------
# A1. WaveTrend (alpha-engine-v21 口径: N1=50, N2=105)
# ----------------------------------------------------------------------------

def algo_wavetrend(df: pd.DataFrame) -> list[AlgoResult]:
    out = []
    def wt(close, n1=50, n2=105, sig=4):
        esa = close.ewm(span=n1, adjust=False).mean()
        d = (close - esa).abs().ewm(span=n1, adjust=False).mean()
        ci = (close - esa) / (0.015 * d)
        wt1 = ci.ewm(span=n2, adjust=False).mean()
        wt2 = wt1.rolling(sig).mean()
        return wt1, wt2

    # 日线
    wt1, wt2 = wt(df["close"])
    v1, v2 = float(wt1.iloc[-1]), float(wt2.iloc[-1])
    cross = "死叉形成中" if v1 < v2 else "金叉/多头"
    d = -1 if v1 < v2 else (1 if v1 > 0 else 0)
    out.append(AlgoResult(
        "WaveTrend 日线", "momentum", "short", d, min(abs(v1) / 60, 1),
        {"wt1": round(v1, 2), "wt2": round(v2, 2), "cross": cross,
         "pct_rank_1y": round(float((wt1.tail(250) < v1).mean() * 100), 1)},
        "V21 口径 N1=50 N2=105; WT1 必须用完整历史"))

    # 月度采样: V21 口径 = 日线计算 WT 后按月取月末值 (NOT 在月线上重算)
    tmp = pd.DataFrame({"date": df["date"].values, "wt1": wt1.values})
    tmp["ym"] = tmp["date"].dt.to_period("M")
    mw = tmp.groupby("ym")["wt1"].last()
    mv = float(mw.iloc[-1])
    d = 1 if mv > -30 else (-1 if mv < -60 else 0)
    out.append(AlgoResult(
        "WaveTrend 月度", "momentum", "long", d, min(abs(mv) / 60, 1),
        {"wt1_monthly": round(mv, 2),
         "history_12m": {str(k): round(float(v), 2) for k, v in mw.tail(12).items()},
         "note": ">+60 动量延续(LAW-001); <-60 低WT1非反转(LAW-001)"},
        "LAW-001: 高WT1动量延续, 低WT1非反转"))
    return out


# ----------------------------------------------------------------------------
# A2. 技术三维投票 (EMA/ADX + BB/RSI + OBV)
# ----------------------------------------------------------------------------

def algo_technical_basic(df: pd.DataFrame) -> AlgoResult:
    H, L, C, V = df["high"], df["low"], df["close"], df["volume"]
    ema12, ema26 = C.ewm(span=12).mean(), C.ewm(span=26).mean()
    tr = pd.concat([H - L, (H - C.shift()).abs(), (L - C.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    up, dn = H.diff(), -L.diff()
    pdm = np.where((up > dn) & (up > 0), up, 0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0)
    pdi = 100 * pd.Series(pdm, index=df.index).rolling(14).mean() / atr
    mdi = 100 * pd.Series(mdm, index=df.index).rolling(14).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    adx = dx.rolling(14).mean()
    delta = C.diff()
    g = delta.clip(lower=0).rolling(14).mean()
    ls = (-delta.clip(upper=0)).rolling(14).mean()
    rsi = 100 - 100 / (1 + g / ls)
    bb_mid, bb_std = C.rolling(20).mean(), C.rolling(20).std()
    bbp = (C.iloc[-1] - bb_mid.iloc[-1]) / (2 * bb_std.iloc[-1])
    obv = (np.sign(C.diff()) * V).fillna(0).cumsum()
    vr = V / V.rolling(20).mean()

    tv = 1 if (ema12.iloc[-1] > ema26.iloc[-1] and adx.iloc[-1] > 20) else \
         (-1 if (ema12.iloc[-1] < ema26.iloc[-1] and adx.iloc[-1] > 20) else 0)
    rv = float(rsi.iloc[-1])
    mv = -1 if (rv > 70 or bbp > 1) else (1 if (rv < 30 or bbp < -1) else 0)
    obv_slope = float(obv.diff(10).iloc[-1])
    vv = 1 if (obv_slope > 0 and vr.iloc[-1] > 1) else (-1 if (obv_slope < 0 and vr.iloc[-1] > 1) else 0)
    comp = tv + mv + vv
    return AlgoResult(
        "技术三维投票", "momentum", "mid", int(np.sign(comp)), min(abs(comp) / 3, 1),
        {"trend_vote": tv, "mr_vote": mv, "vol_vote": vv, "composite": comp,
         "ema12": round(float(ema12.iloc[-1]), 2), "ema26": round(float(ema26.iloc[-1]), 2),
         "adx": round(float(adx.iloc[-1]), 1), "rsi": round(rv, 1), "bb_pct_b": round(float(bbp), 2)},
        "趋势+均值回归+量价三维投票")


# ----------------------------------------------------------------------------
# B1. 蜡烛图 (TA-Lib, 15 patterns)
# ----------------------------------------------------------------------------

CANDLE_PATTERNS = {
    "CDLHAMMER": ("锤子", "bull"), "CDLINVERTEDHAMMER": ("倒锤", "bull"),
    "CDLSHOOTINGSTAR": ("射击之星", "bear"), "CDLDOJI": ("十字星", "neutral"),
    "CDLSPINNINGTOP": ("陀螺", "neutral"), "CDLENGULFING": ("吞没", "both"),
    "CDLHARAMI": ("孕线", "both"), "CDLDARKCLOUDCOVER": ("乌云盖顶", "bear"),
    "CDLPIERCING": ("刺透", "bull"), "CDLMORNINGSTAR": ("启明星", "bull"),
    "CDLEVENINGSTAR": ("黄昏星", "bear"), "CDL3WHITESOLDIERS": ("三白兵", "bull"),
    "CDL3BLACKCROWS": ("三黑鸦", "bear"), "CDLHANGINGMAN": ("上吊", "bear"),
    "CDLMARUBOZU": ("光头光脚", "neutral"),
}


def algo_candlestick(df: pd.DataFrame, lookback: int = 10) -> AlgoResult:
    try:
        import talib
    except ImportError:
        return AlgoResult("蜡烛图", "pattern", "short", 0, 0, {}, "TA-Lib 未安装", ok=False)
    O = df["open"].values.astype(float)
    H = df["high"].values.astype(float)
    L = df["low"].values.astype(float)
    C = df["close"].values.astype(float)
    hits = []
    bull = bear = 0
    for code, (name, kind) in CANDLE_PATTERNS.items():
        fn = getattr(talib, code, None)
        if fn is None:
            continue
        sig = pd.Series(fn(O, H, L, C), index=df["date"])
        recent = sig.tail(lookback)
        for dt, val in recent[recent != 0].items():
            hits.append({"date": str(pd.Timestamp(dt).date()), "pattern": name, "value": int(val)})
            if val > 0:
                bull += 1
            else:
                bear += 1
    d = int(np.sign(bull - bear))
    return AlgoResult(
        "蜡烛图", "pattern", "short", d, min(abs(bull - bear) / 5, 1),
        {"recent_hits": hits[-8:], "bull_count": bull, "bear_count": bear,
         "note": "仅最近 %d 根K线" % lookback},
        "TA-Lib 15 形态")


# ----------------------------------------------------------------------------
# B2. 缠论 (czsc)
# ----------------------------------------------------------------------------

def algo_chanlun(df: pd.DataFrame) -> AlgoResult:
    try:
        from czsc import CZSC, RawBar, Freq
    except ImportError:
        return AlgoResult("缠论", "pattern", "short", 0, 0, {}, "czsc 未安装", ok=False)
    bars = [RawBar(symbol="X", id=i, dt=pd.Timestamp(df["date"].iloc[i]).to_pydatetime(), freq=Freq.D,
                   open=float(df["open"].iloc[i]), close=float(df["close"].iloc[i]),
                   high=float(df["high"].iloc[i]), low=float(df["low"].iloc[i]),
                   vol=float(df["volume"].iloc[i]), amount=float(df["volume"].iloc[i] * df["close"].iloc[i]))
            for i in range(len(df))]
    c = CZSC(bars, max_bi_num=50)
    fx = c.fx_list[-1]
    bis = c.bi_list
    # 手动中枢 (3 笔重叠)
    zs = []
    i = 0
    while i <= len(bis) - 3:
        a, b, cc = bis[i], bis[i + 1], bis[i + 2]
        zg = min(a.high, b.high, cc.high)
        zd = max(a.low, b.low, cc.low)
        if zg > zd:
            zs.append({"sdt": str(a.fx_a.dt.date()), "edt": str(cc.fx_b.dt.date()),
                       "zg": round(zg, 2), "zd": round(zd, 2)})
            i += 3
        else:
            i += 1
    price = float(df["close"].iloc[-1])
    in_zs = False
    if zs:
        cur = zs[-1]
        in_zs = cur["zd"] <= price <= cur["zg"]
    is_top = "顶" in str(fx.mark)
    # 顶分型 -> 潜在卖; 底分型 -> 潜在买
    d = -1 if is_top else 1
    return AlgoResult(
        "缠论", "pattern", "short", d, 0.6,
        {"latest_fx": f"{fx.mark} @ {fx.dt.date()} ({fx.fx:.2f})",
         "bi_count": len(bis), "zs_count": len(zs),
         "latest_zs": zs[-1] if zs else None, "price_in_zs": in_zs,
         "current_bi": f"{bis[-1].direction.value} {bis[-1].fx_a.fx:.2f}->{bis[-1].fx_b.fx:.2f}"},
        "顶分型=潜在卖 / 底分型=潜在买; 中枢内=无趋势")


# ----------------------------------------------------------------------------
# B3. 艾略特波浪 (Zigzag + 5 浪)
# ----------------------------------------------------------------------------

def _find_swings(H: pd.Series, L: pd.Series, dates: pd.Series, w: int = 10) -> list:
    fw = w * 2 + 1
    rmax = H.rolling(fw, center=True).max()
    rmin = L.rolling(fw, center=True).min()
    raw = []
    for i in range(len(H)):
        is_h = bool(H.iloc[i] == rmax.iloc[i])
        is_l = bool(L.iloc[i] == rmin.iloc[i])
        if is_h and not is_l:
            raw.append({"idx": pd.Timestamp(dates.iloc[i]), "price": float(H.iloc[i]), "type": "H"})
        elif is_l and not is_h:
            raw.append({"idx": pd.Timestamp(dates.iloc[i]), "price": float(L.iloc[i]), "type": "L"})
    if not raw:
        return []
    zz = [raw[0]]
    for pt in raw[1:]:
        if pt["type"] == zz[-1]["type"]:
            if pt["type"] == "H" and pt["price"] > zz[-1]["price"]:
                zz[-1] = pt
            elif pt["type"] == "L" and pt["price"] < zz[-1]["price"]:
                zz[-1] = pt
        else:
            zz.append(pt)
    return zz


def algo_elliott(df: pd.DataFrame) -> AlgoResult:
    sw = _find_swings(df["high"], df["low"], df["date"], 10)
    if len(sw) < 6:
        return AlgoResult("艾略特波浪", "pattern", "mid", 0, 0, {"swings": len(sw)}, "swing 不足")
    seg = sw[-6:]
    types = [s["type"] for s in seg]
    diffs = [round(seg[i + 1]["price"] - seg[i]["price"], 2) for i in range(5)]
    d, pattern = 0, "未形成标准5浪"
    if types == ["L", "H", "L", "H", "L", "H"]:
        d, pattern = -1, "看涨推动浪完成 (5浪上升 → 潜在见顶)"
    elif types == ["H", "L", "H", "L", "H", "L"]:
        d, pattern = 1, "看跌推动浪完成 (5浪下跌 → 潜在见底)"
    return AlgoResult(
        "艾略特波浪", "pattern", "mid", d, 0.5,
        {"swings": [{"date": str(s["idx"].date()), "type": s["type"], "price": round(s["price"], 2)} for s in sw[-6:]],
         "types": types, "segments": diffs, "pattern": pattern},
        "Zigzag + 5浪 + 斐波那契")


# ----------------------------------------------------------------------------
# B4. 谐波形态 (XABCD)
# ----------------------------------------------------------------------------

def algo_harmonic(df: pd.DataFrame) -> AlgoResult:
    sw = _find_swings(df["high"], df["low"], df["date"], 10)
    ratios = {"Gartley": (0.618, 0.786), "Bat": (0.45, 0.886),
              "Butterfly": (0.786, 1.27), "Crab": (0.5, 1.618)}
    found = []
    for i in range(len(sw) - 4):
        pts = sw[i:i + 5]
        X, A, B, Cc, D = [p["price"] for p in pts]
        types = [p["type"] for p in pts]
        XA, AB, BC = abs(A - X), abs(B - A), abs(Cc - B)
        if XA == 0 or AB == 0 or BC == 0:
            continue
        rB, rD = AB / XA, abs(D - Cc) / BC
        for name, (rb, rd) in ratios.items():
            if abs(rB - rb) < 0.10 and abs(rD - rd) < 0.15:
                found.append({"pattern": name, "dir": "bear" if types[0] == "H" else "bull",
                              "start": str(pts[0]["idx"].date()), "end": str(pts[-1]["idx"].date()),
                              "D": round(D, 2), "B_XA": round(rB, 3), "D_XC": round(rD, 3)})
    # 只看最近 120 天内的
    recent = [f for f in found if pd.Timestamp(f["end"]) > df["date"].iloc[-1] - pd.Timedelta(days=120)]
    d = 0
    if recent:
        d = -1 if recent[-1]["dir"] == "bear" else 1
    return AlgoResult(
        "谐波形态", "pattern", "mid", d, 0.5,
        {"all_matches": found[-5:], "recent_120d": recent},
        "XABCD 斐波那契几何")


# ----------------------------------------------------------------------------
# C1. SMC / ICT
# ----------------------------------------------------------------------------

def algo_smc(df: pd.DataFrame) -> AlgoResult:
    try:
        import smartmoneyconcepts as smc
    except ImportError:
        return AlgoResult("SMC/ICT", "structure", "short", 0, 0, {}, "smartmoneyconcepts 未安装", ok=False)
    d2 = df.rename(columns={"open": "Open", "high": "High", "low": "Low",
                            "close": "Close", "volume": "Volume"})[
        ["Open", "High", "Low", "Close", "Volume"]].copy()
    dates = d2.index
    sw = smc.smc.swing_highs_lows(d2, swing_length=10)
    bos = smc.smc.bos_choch(d2, sw, close_break=True)
    fvg = smc.smc.fvg(d2)
    ob = smc.smc.ob(d2, sw)
    rb = bos[bos["BOS"].notna()] if "BOS" in bos.columns else bos.iloc[0:0]
    last_bos = None
    if len(rb):
        for pos, row in rb.tail(1).iterrows():
            dt = df["date"].iloc[pos] if pos < len(df) else pos
            last_bos = {"date": str(pd.Timestamp(dt).date()), "dir": "bull" if row["BOS"] > 0 else "bear",
                        "level": round(float(row["Level"]), 2)}
    rf = fvg[fvg["FVG"].notna()] if "FVG" in fvg.columns else fvg.iloc[0:0]
    last_fvg = []
    for pos, row in rf.tail(3).iterrows():
        dt = df["date"].iloc[pos] if pos < len(df) else pos
        last_fvg.append({"date": str(pd.Timestamp(dt).date()),
                         "dir": "bull" if row["FVG"] > 0 else "bear",
                         "range": [round(float(row["Bottom"]), 2), round(float(row["Top"]), 2)]})
    rob = ob[ob["OB"].notna()] if "OB" in ob.columns else ob.iloc[0:0]
    last_ob = []
    for pos, row in rob.tail(2).iterrows():
        dt = df["date"].iloc[pos] if pos < len(df) else pos
        last_ob.append({"date": str(pd.Timestamp(dt).date()),
                        "dir": "bull" if row["OB"] > 0 else "bear",
                        "range": [round(float(row["Bottom"]), 2), round(float(row["Top"]), 2)]})
    d = -1 if (last_bos and last_bos["dir"] == "bear") else (1 if last_bos else 0)
    return AlgoResult(
        "SMC/ICT", "structure", "short", d, 0.5,
        {"last_bos": last_bos, "recent_fvg": last_fvg, "recent_ob": last_ob,
         "swing_points": int(sw.dropna().shape[0])},
        "BOS=趋势延续 / ChoCH=反转 / FVG=回补目标 / OB=机构挂单区")


# ----------------------------------------------------------------------------
# C2. 一目均衡表 (Ichimoku)
# ----------------------------------------------------------------------------

def algo_ichimoku(df: pd.DataFrame) -> AlgoResult:
    H, L, C = df["high"], df["low"], df["close"]
    def don(p):
        return (H.rolling(p).max() + L.rolling(p).min()) / 2
    tenkan, kijun = don(9), don(26)
    spanA = ((tenkan + kijun) / 2).shift(26)
    spanB = don(52).shift(26)
    top = pd.concat([spanA, spanB], axis=1).max(axis=1)
    bot = pd.concat([spanA, spanB], axis=1).min(axis=1)
    price = float(C.iloc[-1])
    if price > top.iloc[-1]:
        pos = "云上方"
    elif price < bot.iloc[-1]:
        pos = "云下方"
    else:
        pos = "云内"
    cloud = "bull" if spanA.iloc[-1] > spanB.iloc[-1] else "bear"
    tk = "bull" if tenkan.iloc[-1] > kijun.iloc[-1] else "bear"
    d = 1 if (pos == "云上方" and cloud == "bull" and tk == "bull") else \
        (-1 if (pos == "云下方" and cloud == "bear" and tk == "bear") else 0)
    return AlgoResult(
        "一目均衡表", "structure", "mid", d, 0.5,
        {"tenkan": round(float(tenkan.iloc[-1]), 2), "kijun": round(float(kijun.iloc[-1]), 2),
         "cloud_top": round(float(top.iloc[-1]), 2), "cloud_bottom": round(float(bot.iloc[-1]), 2),
         "price_pos": pos, "cloud_dir": cloud, "tk": tk},
        "五线系统: 云位置 + 云方向 + TK 三重过滤")



# ----------------------------------------------------------------------------
# C3. 江恩理论 (Gann) — 复用 gann skill 的 analyze_gann
# ----------------------------------------------------------------------------

def algo_gann(df: pd.DataFrame) -> AlgoResult:
    """Gann angles / Square of 9 / Time-price squaring / Rule of 7 / 50% rule."""
    import importlib.util
    from pathlib import Path
    cand = list(Path(__file__).resolve().parents[3].glob(
        "skills/vibe-trading-gann/examples/spcx_analysis.py"))
    if not cand:
        return AlgoResult("江恩理论", "structure", "mid", 0, 0, {}, "gann skill 未找到", ok=False)
    try:
        spec = importlib.util.spec_from_file_location("gann_mod", cand[0])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        g = mod.analyze_gann(df)
    except Exception as e:
        return AlgoResult("江恩理论", "structure", "mid", 0, 0, {},
                          f"{type(e).__name__}: {e}", ok=False)
    price = float(df["close"].iloc[-1])
    # 方向判定: 收盘价相对 50% 中轴 + 1x1 角
    mid = g.get("50pct_midpoint")
    d = 0
    if isinstance(mid, (int, float)):
        d = 1 if price > mid else -1
    return AlgoResult(
        "江恩理论", "structure", "mid", d, 0.4,
        {"50pct_midpoint": mid, "distance_to_50pct_pct": g.get("distance_to_50pct_pct"),
         "sq9_current": g.get("sq9_current"), "rule_of_7": g.get("rule_of_7"),
         "overall_high": g.get("overall_high"), "overall_low": g.get("overall_low")},
        "Gann: 角度线/Square of 9/时间价格正方/7 规则/50% 法则")

# ----------------------------------------------------------------------------
# D. 汇总裁决
# ----------------------------------------------------------------------------

def synthesize(results: list[AlgoResult]) -> dict:
    ok = [r for r in results if r.ok]
    price_algos = [r for r in ok if r.layer in ("momentum", "pattern", "structure")]
    votes = [r.direction for r in ok]
    bull = sum(1 for v in votes if v > 0)
    bear = sum(1 for v in votes if v < 0)
    neu = sum(1 for v in votes if v == 0)
    weighted = sum(r.direction * r.strength for r in ok)
    by_scale = {}
    for r in ok:
        by_scale.setdefault(r.scale, []).append(r.direction)
    scale_view = {k: int(np.sign(sum(v))) for k, v in by_scale.items()}
    return {
        "n_algorithms": len(ok),
        "bull": bull, "bear": bear, "neutral": neu,
        "weighted_score": round(weighted, 2),
        "consensus": "偏多" if bull > bear + 1 else ("偏空" if bear > bull + 1 else "中性/分歧"),
        "scale_view": scale_view,
        "independence_caveat": (
            f"{len(price_algos)}/{len(ok)} 个算法均基于同一 OHLCV 价格序列 —— "
            "这是同一数据的多种变换, 不是相互独立的证据。独立验证需成交量/资金流/基本面等非价格维度。"
        ),
    }


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def run(args) -> dict:
    df = load_data(args)
    df = df.sort_values("date").reset_index(drop=True)
    if len(df) < 60:
        raise RuntimeError(f"bars 不足 ({len(df)} < 60)")

    results: list[AlgoResult] = []
    runners = [
        ("A1 WaveTrend", lambda: algo_wavetrend(df)),
        ("A2 技术三维投票", lambda: [algo_technical_basic(df)]),
        ("B1 蜡烛图", lambda: [algo_candlestick(df)]),
        ("B2 缠论", lambda: [algo_chanlun(df)]),
        ("B3 艾略特波浪", lambda: [algo_elliott(df)]),
        ("B4 谐波形态", lambda: [algo_harmonic(df)]),
        ("C1 SMC/ICT", lambda: [algo_smc(df)]),
        ("C2 一目均衡表", lambda: [algo_ichimoku(df)]),
        ("C3 江恩理论", lambda: [algo_gann(df)]),
    ]
    for label, fn in runners:
        try:
            results.extend(fn())
        except Exception as e:
            results.append(AlgoResult(label, "unknown", "short", 0, 0, {}, f"{type(e).__name__}: {e}", ok=False))

    summary = synthesize(results)
    last = df.iloc[-1]
    payload = {
        "meta": {
            "code": args.code, "market": args.market,
            "date_range": [str(df["date"].iloc[0].date()), str(df["date"].iloc[-1].date())],
            "bars": len(df),
            "last_close": round(float(last["close"]), 2),
        },
        "summary": summary,
        "algorithms": [asdict(r) for r in results],
    }
    return payload


def main():
    ap = argparse.ArgumentParser(description="多算法趋势分析")
    ap.add_argument("--code", default="601788")
    ap.add_argument("--market", default="sh", choices=["sh", "sz", "bj"])
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    ap.add_argument("--csv", default=None, help="本地 CSV (date,open,high,low,close,volume)")
    ap.add_argument("--bars", type=int, default=None, help="(预留) 最大 bars")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    payload = run(args)

    # 文本摘要
    m = payload["meta"]
    s = payload["summary"]
    print("=" * 64)
    print(f"多算法趋势分析 — {m['code']} ({m['date_range'][0]} → {m['date_range'][1]}, {m['bars']} bars)")
    print("=" * 64)
    print(f"最新收盘: {m['last_close']}")
    print(f"\n信号统计: 偏多 {s['bull']} / 中性 {s['neutral']} / 偏空 {s['bear']}  →  {s['consensus']}")
    print(f"加权分数: {s['weighted_score']}   时间尺度: {s['scale_view']}")
    print("\n" + "-" * 64)
    for a in payload["algorithms"]:
        if not a["ok"]:
            print(f"[SKIP] {a['name']:16s} {a['note']}")
            continue
        arrow = "▲多" if a["direction"] > 0 else ("▼空" if a["direction"] < 0 else "―中")
        print(f"[{arrow}] {a['name']:16s} [{a['layer']}/{a['scale']}] strength={a['strength']:.2f}")
        print(f"        {a['note']}")
        for k, v in a["readings"].items():
            if k in ("recent_hits", "swings", "all_matches", "recent_fvg", "recent_ob"):
                continue
            print(f"          · {k}: {v}")
    print("-" * 64)
    print(f"\n⚠ 独立性质检: {s['independence_caveat']}")

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\nJSON 已写入 {args.json_out}")


if __name__ == "__main__":
    main()
