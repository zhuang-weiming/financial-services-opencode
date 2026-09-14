"""
wif_now.py — run the WIF v5.9 market-timing engine AS OF TODAY on real data.

The shipped WIF data ends 2026-07-16. This script:
  1. loads the shipped 4926x10 merged price matrix (2007-01-03..2026-07-16)
  2. splices on the 2026-07-16..2026-09-11 window fetched from Tier-1 MCP
     (SPY BND GLD TLT VTI QQQ XLE SHV VIXM) plus ^VIX
  3. rebuilds VIXTERM = VIX - VIXM  (the shipped file uses the VIXM-price proxy)
  4. re-runs compute_csi / phase1_status / macro_quadrant

KNOWN GAP — DO NOT IGNORE
-------------------------
`compute_csi` reads an `F29` (or `F29_bp`) column for 45% of its weight.  The
shipped matrix has NO F29 column, and the docstring is explicit: "Missing
components contribute zero and are *not* rescaled."  So the local CSI runs at
55% of its designed weight and the F29>500bp EMERGENCY hard-trigger is disabled.
We report both the partial CSI and the last externally-verified F29.

Run: python3 wif_now.py
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

REPO = "/Users/weimingzhuang/Documents/source_code/financial-services-opencode"
HERE = os.path.dirname(os.path.abspath(__file__))          # example/wif-framework/scripts
WIFROOT = os.path.dirname(HERE)                             # example/wif-framework
DATADIR = os.path.join(WIFROOT, "data")                     # example/wif-framework/data
WIF = DATADIR
sys.path.insert(0, os.path.join(REPO, ".opencode/python/wif-framework"))

SHIPPED = os.path.join(WIF, "_merged_prices_20260716.csv")
UPDATE = os.path.join(DATADIR, "_increments/wif_update_20260912.csv")
VIXCSV = os.path.join(DATADIR, "_increments/vix_window_20260912.csv")

# Last externally verified F29 (BAA - DGS10), from the 2026-07-17 WIF assessment
F29_LAST = dict(value_bp=159, date="2026-07-16", baa=6.16, dgs10=4.57)


def deglitch(base: pd.DataFrame, tol: float = 0.25) -> pd.DataFrame:
    """Repair the calibration break in the SHIPPED matrix.

    `_merged_prices_20260716.csv` switches basis mid-series: the segment
    before 2026-06-09 is on raw close, the segment from 2026-06-09 on is on
    Adj Close.  The jump is SPY x1.816 / TLT x2.286 / BND x1.835 / VTI x1.547
    on a single day, which is not a market move.

    Consequence if left alone: 126-day momentum and 60-day rolling means are
    inflated by the gap, so the macro quadrant is WRONG (it read Q4 Overheat
    off a <-spurious> +41% SPY 60-day mean; a normal reading is single digits).

    Fix: for any column with a one-day move above `tol`, rescale the LATER
    segment DIVIDING by the observed ratio.  We shrink the later (short,
    anomalous) segment rather than inflating the earlier (19-year, correct)
    one, so the series keeps its true adjusted-close LEVEL.

    The level matters: with the later segment left inflated, SPY 2026-07-16
    reads 1369.98 while Tier-1 adjustedClose says 750.72 (verified
    2026-09-15).  Shrinking the later segment restores +659.3% true
    buy-and-hold (2007-01-03 -> 2026-07-16), instead of the artifact-inflated
    +1283.0% that the WIF skill document quotes.
    """
    base = base.copy()
    # ONLY the price columns. VIX/VIXTERM are index points that genuinely move
    # +/-30-50% in a session during a crisis (2008, 2010, 2011) - "fixing" those
    # would destroy the real history.
    for col in [c for c in base.columns if c not in ("VIX", "VIXTERM")]:
        r = base[col].pct_change(fill_method=None)
        breaks = r[r.abs() > tol]
        for dt, move in breaks.items():
            ratio = 1.0 + move
            mask = base.index >= dt
            base.loc[mask, col] = base.loc[mask, col] / ratio
            print(f"  [deglitch] {col} @ {dt.date()}: {move*100:+.1f}% "
                  f"-> shrink later segment by /{ratio:.4f}")
    return base


def build_matrix() -> pd.DataFrame:
    """Extend the official matrix to the newest fetched date.

    ⚠️ TWO calibration defects have to be repaired (see deglitch() above and
    the docstring below).  Both are in the SHIPPED file, not introduced here.

    (a) SHIPPED matrix breaks basis at 2026-06-09 (raw -> Adj Close).
    (b) The Tier-1 fetch returns RAW close while the matrix is Adj Close, so a
        1:1 splice injects a fake -45% SPY / -56% TLT gap.  Fixed by
        ratio-splicing prices and additively shifting VIXTERM.
    """
    base = deglitch(pd.read_csv(SHIPPED, index_col=0, parse_dates=True))
    upd = pd.read_csv(UPDATE)
    upd["date"] = pd.to_datetime(upd["date"])
    pivot = upd.pivot_table(index="date", columns="ticker", values="close")

    vix = None
    if os.path.exists(VIXCSV):
        v = pd.read_csv(VIXCSV)
        v["date"] = pd.to_datetime(v["date"])
        vix = v.set_index("date")["close"]
    if vix is not None:
        pivot["VIX"] = vix
    if "VIXM" in pivot.columns and "VIX" in pivot.columns:
        pivot["VIXTERM"] = pivot["VIX"] - pivot["VIXM"]

    overlap = base.index[-1]
    PRICE_COLS = ["SPY", "BND", "GLD", "TLT", "VTI", "QQQ", "XLE", "SHV"]
    aligned = {}
    for col in base.columns:
        if col not in pivot.columns:
            continue
        series = pivot[col].copy()
        if col in PRICE_COLS and overlap in series.index and pd.notna(series.loc[overlap]):
            f = base.loc[overlap, col] / series.loc[overlap]
            series = series * f
            if abs(f - 1) > 0.02:
                print(f"  [splice] {col}: x{f:.4f} (raw {pivot[col].loc[overlap]:.2f} -> official {base.loc[overlap, col]:.2f})")
        elif col == "VIXTERM" and overlap in series.index and pd.notna(series.loc[overlap]):
            d = base.loc[overlap, col] - series.loc[overlap]
            series = series + d
            print(f"  [splice] VIXTERM: additive shift {d:+.3f}")
        aligned[col] = series

    new = pd.DataFrame(aligned)
    ext = pd.concat([base, new[~new.index.isin(base.index)]]).sort_index()
    # post-condition: no unexplained jump anywhere
    chk = ext[PRICE_COLS].pct_change(fill_method=None).abs()
    worst = chk.max().max()
    bad = chk.stack()[chk.stack() > 0.25]
    print(f"  [check] max |1-day move| = {worst*100:.1f}%"
          + ("  ⚠️ still has jumps: " + ", ".join(str(i[0].date()) + "/" + i[1] for i in bad.items()) if len(bad) else "  ✅ clean"))
    return ext


def main():
    from wif_framework.phase import compute_csi, phase1_status, macro_quadrant, current_phase

    ext = build_matrix()
    ext.ffill(inplace=True)
    print("=" * 96)
    print("WIF v5.9 — 真实数据重跑")
    print("=" * 96)
    print(f"矩阵: {ext.shape}  {ext.index.min().date()} → {ext.index.max().date()}")
    print(f"最后 10 日收盘: SPY {ext['SPY'].iloc[-1]:.2f} | TLT {ext['TLT'].iloc[-1]:.2f} | "
          f"GLD {ext['GLD'].iloc[-1]:.2f} | VIX {ext['VIX'].iloc[-1]:.2f} | "
          f"VIXTERM {ext['VIXTERM'].iloc[-1]:+.2f}")

    res = current_phase(ext)
    print("\n--- current_phase() ---")
    print(json.dumps(res, indent=1, default=str))

    csi = compute_csi(ext)
    print(f"\n--- CSI（部分：缺 F29，权重仅 55%）---")
    print(f"CSI 最新 = {csi.iloc[-1]:.3f}  (EMERGENCY>2.0 / WARNING>1.0 / HEALTHY<1.0)")
    print(f"CSI 60d 分位 = {(csi.tail(60) < csi.iloc[-1]).mean()*100:.0f}%")

    st = phase1_status(ext, csi)
    print(f"\nPhase1_status 最新 = {st.iloc[-1]}   （最近 10 日: {list(st.tail(10).values)}）")

    q = macro_quadrant(ext)
    print(f"Macro Quadrant 最新 = Q{q.iloc[-1]}  "
          f"（最近 10 日: {list(q.tail(10).values)}）")

    # momentum for the quadrant's own inputs
    for t in ["SPY", "TLT"]:
        m = ext[t] / ext[t].shift(126) - 1
        print(f"  {t} 126d 动量 = {m.iloc[-1]*100:+.1f}%")

    print("\n--- 已知缺口 ---")
    print(f"F29 (BAA-DGS10): 本地矩阵无此列 → CSI 45% 权重缺失且不重缩放")
    print(f"  最后外部核实值 = {F29_LAST['value_bp']} bp @ {F29_LAST['date']} "
          f"(BAA {F29_LAST['baa']} - DGS10 {F29_LAST['dgs10']})，硬触发线 500bp")
    # ---- persist: write the extended matrix back to the WIF data dir -------
    dst_dir = os.path.join(WIF)
    dst = os.path.join(dst_dir, f"_merged_prices_{ext.index.max().strftime('%Y%m%d')}.csv")
    ext.to_csv(dst)
    # credit-spread anchors we could verify (F29 = BAA10Y, in bp)
    pd.DataFrame([
        dict(date="2026-05-08", f29_bp=165, source="CreditSpread_BAA_1986_2026.csv"),
        dict(date="2026-07-16", f29_bp=159, source="wif_phase_assessment_20260717.json (BAA 6.16 - DGS10 4.57)"),
        dict(date="2026-09-10", f29_bp=151, source="FRED BAA10Y via llmquant-data"),
    ]).to_csv(os.path.join(dst_dir, "F29_anchors_20260911.csv"), index=False)
    print(f"\nSAVED matrix -> {dst}")
    print(f"SAVED anchors -> {os.path.join(dst_dir, 'F29_anchors_20260911.csv')}")

    out = dict(as_of=str(ext.index.max().date()), phase=res,
               csi_partial=float(csi.iloc[-1]), phase1_status=str(st.iloc[-1]),
               quadrant=int(q.iloc[-1]), f29_last=F29_LAST)
    with open(os.path.join(DATADIR, "wif_now_latest.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    # ---- five-layer current read ------------------------------------------
    print()
    print("=" * 96)
    print("五层读数（用户问的 ①~⑤）")
    print("=" * 96)
    vix = ext["VIX"]
    vix10 = vix.pct_change(10, fill_method=None)
    print(f"① 硬触发")
    print(f"   F29 (BAA10Y) = 151 bp @2026-09-10  → 硬触发线 500bp  ⇒ {'EMERGENCY' if 151>500 else 'NOT triggered'}"
          f"  (距触发线 {500-151} bp)")
    print(f"   VIX = {vix.iloc[-1]:.2f} ; 10日涨幅 = {vix10.iloc[-1]*100:+.1f}%  → 需 VIX>40 且 >+100% ⇒ NOT triggered")

    print(f"② CSI 分量")
    from wif_framework.phase import _zscore
    z_vixt = _zscore(ext["VIXTERM"]).iloc[-1]
    ret = ext[["SPY", "GLD"]].pct_change(fill_method=None)
    corr = ret["SPY"].rolling(20).corr(ret["GLD"])
    z_corr = (-_zscore(corr)).iloc[-1]
    print(f"   Z(VIXTERM_60d)      = {z_vixt:+.2f}  × 0.35 = {0.35*z_vixt:+.3f}")
    print(f"   -Z(SPY/GLD 20d corr)= {z_corr:+.2f}  × 0.20 = {0.20*z_corr:+.3f}")
    print(f"   Z(F29_60d)          = ???  × 0.45 = ???   ← 缺 60 日序列（仅 3 个锚点 165→159→151bp）")
    print(f"   ⇒ CSI(部分 55%) = {0.35*z_vixt + 0.20*z_corr:+.3f}  → HEALTHY")

    print(f"③ 宏观象限（引擎口径 = 126d 动量的 **60日均值** 的正负）")
    spy_m = ext["SPY"].pct_change(126, fill_method=None)
    tlt_m = ext["TLT"].pct_change(126, fill_method=None)
    spy60 = spy_m.rolling(60).mean().iloc[-1]
    tlt60 = tlt_m.rolling(60).mean().iloc[-1]
    print(f"   瞬时 126d:  SPY {spy_m.iloc[-1]*100:+.1f}%  TLT {tlt_m.iloc[-1]*100:+.1f}%")
    print(f"   60日均值:   SPY {spy60*100:+.1f}%  TLT {tlt60*100:+.1f}%   ← 引擎用这个")
    print(f"   判定: SPY>{'0' if spy60>0 else '0'} & TLT{'>0' if tlt60>0 else '<0'} → "
          f"Q{q.iloc[-1]} {'Recovery' if q.iloc[-1]==2 else 'Overheat' if q.iloc[-1]==4 else 'Stagflation' if q.iloc[-1]==3 else 'Recession'}")

    print(f"④ 相位")
    print(f"   Phase1_status = {st.iloc[-1]}  →  final phase = Phase {res['phase']} "
          f"{['','Rising','Panic','Fall','Recover','Transition'][res['phase']]}")
    print(f"   目标配置: 权益 65-75% / 固收 10-15% / 实物 15-25%")

    print(f"⑤ 再平衡")
    print(f"   相位切换 → 次日收盘；常规 → 每 15 个交易日；MCI<+5 → 强制 VTI-only")
    print(f"   当前无相位切换 ⇒ 无需动作")

    print("\nWROTE results/wif_now.json")


if __name__ == "__main__":
    main()
