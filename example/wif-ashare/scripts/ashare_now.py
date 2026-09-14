"""
ashare_now.py — WIF v2.7 (A-share) current read, on fresh data.

Engine: `.opencode/python/wif-framework/wif_framework/ashare.py` (imported, not re-implemented).
Chain:  MCI(PMI, M2) -> 象限 -> MA60 趋势覆盖(±7%) -> R20 EMERGENCY(L1/L2/L3) -> 有效象限 -> 权重

Data freshness
--------------
  macro_pmi.csv          PMI  to 2026-08  (49.8)   <- fresh
  macro_m2_m1_spread.csv M2   to 2026-06  (8.0%)   <- 2 months stale
  HS300                  2026-09-11 (4510.16)     <- Tier-1 Tencent, fresh
  etf_prices_new.csv     to 2026-04-22             <- stale (backtest only)

Run: python3 example/wif-ashare/scripts/ashare_now.py
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

ROOT = "/Users/weimingzhuang/Documents/source_code/financial-services-opencode"
ASH = os.path.join(ROOT, "example/wif-ashare")
DATADIR = os.path.join(ASH, "data")
sys.path.insert(0, os.path.join(ROOT, ".opencode/python/wif-framework"))

from wif_framework.ashare import (compute_mci, mci_to_quadrant, effective_quadrant,
                                  get_em_weight, QW, pmi_norm, m2_norm,
                                  MCI_Q1_THRESH, MCI_Q3_THRESH, TREND_UP, TREND_DOWN)

AS_OF = "2026-09-11"


def main():
    pmi = pd.read_csv(os.path.join(DATADIR, "macro_pmi.csv"))
    m2 = pd.read_csv(os.path.join(DATADIR, "macro_m2_m1_spread.csv"))
    hs = pd.read_csv(os.path.join(DATADIR, "_increments/hs300_tencent_20260911.csv"),
                     parse_dates=["date"])

    pmi_v = float(pmi["PMI"].iloc[-1]); pmi_d = str(pmi["月份"].iloc[-1])[:7]
    m2_v = float(m2["M2_YoY"].iloc[-1]); m2_d = str(m2["月份"].iloc[-1])[:7]
    m1_v = float(m2["M1_YoY"].iloc[-1]); spread = float(m2["Spread"].iloc[-1])

    close = hs.set_index("date")["close"]
    px = float(close.iloc[-1])
    ma60 = float(close.rolling(60).mean().iloc[-1])
    trend = px / ma60 - 1
    r20 = float(px / close.iloc[-21] - 1)

    mci = compute_mci(pmi_v, m2_v)
    q_mci = mci_to_quadrant(mci)
    em_lvl, em_w = get_em_weight(r20)
    q_eff = effective_quadrant(q_mci, trend) if em_lvl is None else q_mci

    print("=" * 96)
    print(f"WIF v2.7（A股）当前读数 — {AS_OF}")
    print("=" * 96)
    print(f"\n【输入】")
    print(f"  PMI         = {pmi_v}  ({pmi_d})   pmi_norm = clamp(({pmi_v}-47)/6) = {0.5*0+0:.0f}{pmi_norm(pmi_v):.4f}")
    print(f"  M2 YoY      = {m2_v}%  ({m2_d})   m2_norm  = clamp(({m2_v}-6)/9) = {m2_norm(m2_v):.4f}")
    print(f"  M1 YoY      = {m1_v}%   M2-M1 剪刀差 = {spread:+.1f}pp")
    print(f"  HS300       = {px:.2f}  MA60 = {ma60:.2f}  → 趋势偏离 = {trend*100:+.2f}%")
    print(f"  R20（20日收益）= {r20*100:+.2f}%")

    print(f"\n【① MCI 与 MCI 象限】")
    print(f"  MCI = 0.5×{pmi_norm(pmi_v):.4f} + 0.5×{m2_norm(m2_v):.4f} = **{mci:.4f}**")
    print(f"  阈值: Q1 ≥ {MCI_Q1_THRESH} | Q3 ≤ {MCI_Q3_THRESH}")
    print(f"  → MCI 象限 = **Q{q_mci}（{'积极' if q_mci==1 else '防御' if q_mci==3 else '过渡'}）**")

    print(f"\n【② MA60 趋势覆盖（±7%）】")
    if trend > TREND_UP:
        print(f"  趋势 {trend*100:+.2f}% > +7% → **强制 Q1**")
    elif trend < TREND_DOWN:
        print(f"  趋势 {trend*100:+.2f}% < -7% → **强制 Q3**")
    else:
        print(f"  趋势 {trend*100:+.2f}% 在 ±7% 内 → **不干预**，保持 MCI 象限")

    print(f"\n【③ EMERGENCY（R20）】")
    if em_lvl:
        print(f"  R20 {r20*100:+.2f}% → **{em_lvl} 触发**（L1<-8% / L2<-12% / L3<-20%）")
    else:
        print(f"  R20 {r20*100:+.2f}% → 未触发（下一级 L1 需 < -8.00%，还有 {(r20+0.08)*100:.2f}pp 距离）")

    print(f"\n【④ 有效象限与目标配置】")
    print(f"  有效象限 = **Q{q_eff}**" + ("（EMERGENCY 覆盖一切）" if em_lvl else ""))
    w = em_w if em_lvl else QW[q_eff]
    print(f"\n  | 资产 | 目标权重 |")
    print(f"  |---|---:|")
    for k, v in sorted(w.items(), key=lambda x: -x[1]):
        print(f"  | {k} | {v*100:.1f}% |")
    eq = sum(v for k, v in w.items() if k in ("hs300", "csi500", "cyb"))
    print(f"\n  股票合计 {eq*100:.1f}% · 黄金 {w.get('gold',0)*100:.1f}% · "
          f"国债 {w.get('bond',0)*100:.1f}% · 现金 {w.get('cash',0)*100:.1f}%")

    out = dict(as_of=AS_OF, pmi=dict(v=pmi_v, date=pmi_d, norm=pmi_norm(pmi_v)),
               m2=dict(v=m2_v, date=m2_d, norm=m2_norm(m2_v), m1=m1_v, spread=spread),
               hs300=dict(px=px, ma60=ma60, trend=trend, r20=r20),
               mci=dict(value=mci, quadrant=q_mci), trend_override=bool(
                   trend > TREND_UP or trend < TREND_DOWN),
               emergency=dict(level=em_lvl, r20=r20), effective_quadrant=q_eff,
               target_weights={k: round(v, 4) for k, v in w.items()})
    with open(os.path.join(DATADIR, f"ashare_assessment_{AS_OF.replace('-','')}.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nWROTE {os.path.join(DATADIR, f'ashare_assessment_{AS_OF.replace(chr(45),chr(0))}.json').replace(chr(0),'')}")


if __name__ == "__main__":
    main()
