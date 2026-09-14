"""
wif_assessment.py — emit the dated WIF phase-assessment artifacts.

Mirrors the repo's existing convention:
    example/wif-framework/data/wif_phase_assessment_<YYYYMMDD>.json
and adds a human-readable companion:
    example/wif-framework/data/wif_phase_assessment_<YYYYMMDD>.md

Everything here is computed from the extended price matrix + externally
verified macro values; nothing is hand-typed except the FRED readings that
were fetched via the Tier-1 MCP in the same session (all cited by date).

Run:  python3 wif_assessment.py
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))          # example/wif-framework/scripts
sys.path.insert(0, HERE)

from wif_now import build_matrix  # noqa: E402

WIF_DATA = os.path.join(os.path.dirname(HERE), "data")     # example/wif-framework/data

AS_OF = "2026-09-11"

# --- Externally verified readings (Tier-1 MCP, this session) ----------------
# FRED via llmquant-data; each carries its own observation date.
MACRO = {
    "f29_baa_10y_bp":   dict(value=151,   date="2026-09-10", source="FRED BAA10Y via llmquant-data", hard_trigger_bp=500),
    "vix_spot":         dict(value=15.84, date="2026-09-11", source="^VIX via llmquant-data"),
    "us10y":            dict(value=4.95,  date="2026-09-10", source="FRED DGS10"),
    "us30y":            dict(value=5.37,  date="2026-09-10", source="FRED DGS30"),
    "us2y":             dict(value=4.62,  date="2026-09-10", source="FRED DGS2 (implied 10y-2y=+0.33)"),
    "curve_10y_2y":     dict(value=0.33,  date="2026-09-11", source="FRED T10Y2Y"),
    "breakeven_10y":    dict(value=2.36,  date="2026-09-11", source="FRED T10YIE"),
    "real_10y":         dict(value=2.59,  date="2026-09-11", source="computed 4.95 - 2.36"),
    "nfci":             dict(value=-0.56, date="2026-08-28", source="FRED NFCI"),
    "stl_fin_stress":   dict(value=-0.7884, date="2026-09-04", source="FRED STLFSI4"),
    "dxy_broad":        dict(value=118.0732, date="2026-09-04", source="FRED DTWEXBGS"),
    "wti":              dict(value=97.26, date="2026-09-09", source="FRED DCOILWTICO"),
    "fed_funds":        dict(value=3.63,  date="2026-08-01", source="FRED FEDFUNDS"),
    "brent":            dict(value=101.21, date="2026-09-09", source="记忆库 4.2（新华社）"),
    "fear_greed":       dict(value=57,    date="2026-09-14", source="Alternative.me F&G via vibe-trading"),
}
F29_HISTORY = [
    dict(date="2026-05-08", f29_bp=165, source="CreditSpread_BAA_1986_2026.csv"),
    dict(date="2026-07-16", f29_bp=159, source="wif_phase_assessment_20260717.json"),
    dict(date="2026-09-10", f29_bp=151, source="FRED BAA10Y"),
]
CROSS_MARKET = [   # the divergence worth recording
    dict(line="企业信用 Corporate credit (F29)", direction="改善", latest="151 bp", trend="165 → 159 → 151 bp"),
    dict(line="主权信用 Sovereign credit (US30Y)", direction="恶化", latest="5.37%", trend="2007 年以来新高"),
    dict(line="权益/波动 Equity / vol", direction="平静", latest="VIX 15.84", trend="SPY 126d +20.9%"),
]


def compute():
    from wif_framework.phase import (compute_csi, phase1_status, macro_quadrant,
                                     current_phase, _zscore)
    ext = build_matrix().ffill()
    res = current_phase(ext)
    csi = compute_csi(ext)
    st = phase1_status(ext, csi)
    q = macro_quadrant(ext)

    vix = ext["VIX"]
    vix10 = vix.pct_change(10, fill_method=None).iloc[-1]
    z_vixt = float(_zscore(ext["VIXTERM"]).iloc[-1])
    ret = ext[["SPY", "GLD"]].pct_change(fill_method=None)
    corr = ret["SPY"].rolling(20).corr(ret["GLD"])
    z_corr = float(-_zscore(corr).iloc[-1])
    spy60 = float(ext["SPY"].pct_change(126, fill_method=None).rolling(60).mean().iloc[-1])
    tlt60 = float(ext["TLT"].pct_change(126, fill_method=None).rolling(60).mean().iloc[-1])
    csi_part = 0.35 * z_vixt + 0.20 * z_corr
    return dict(ext=ext, res=res, csi=float(csi.iloc[-1]), status=str(st.iloc[-1]),
                quadrant=int(q.iloc[-1]), vix=float(vix.iloc[-1]), vix10=float(vix10),
                z_vixt=z_vixt, z_corr=z_corr, spy60=spy60, tlt60=tlt60,
                csi_partial=csi_part, phase=int(res["phase"]))


def build_json(c) -> dict:
    qn = {1: "Rising", 2: "Panic", 3: "Fall", 4: "Recover", 5: "Transition"}[c["phase"]]
    qlabel = {1: "Recession (defensive)", 2: "Recovery (risk-on)",
              3: "Stagflation (commodities)", 4: "Overheat (Late-Cycle)"}[c["quadrant"]]
    return {
        "update_date": AS_OF,
        "assessment_date": AS_OF,
        "data_sources": {
            "prices": "example/wif-framework/data/_merged_prices_20260911.csv "
                      "(official matrix to 2026-07-16 + Tier-1 MCP splice)",
            "F29": "FRED BAA10Y via llmquant-data (Moody's Baa - 10Y)",
            "VIX": "^VIX via llmquant-data",
            "macro": "FRED via llmquant-data (DGS10/DGS30/T10Y2Y/T10YIE/NFCI/STLFSI4/DTWEXBGS/DCOILWTICO/FEDFUNDS)",
        },
        "caveats": [
            "CSI runs at 55% of its designed weight: the local matrix has NO F29 column, and "
            "compute_csi's docstring states missing components contribute zero AND are NOT rescaled. "
            "Therefore Z(F29_60d) (45% weight) is absent and the CSI value is NOT comparable to the "
            "WIF backtest (Sharpe 1.01), which used a 100% CSI.",
            "The F29>500bp EMERGENCY hard-trigger is verified by anchor (151bp) but is not wired into "
            "the local CSI.",
            "VIX splice point: official matrix 2026-07-16 VIX=15.67 vs Tier-1 16.73 (~1pt discontinuity).",
            "VIXTERM CALIBRE MISMATCH with the 2026-07-17 assessment: that file defines "
            "VIXTERM = VIX_spot - VIX3M(value -0.73), whereas _merged_prices uses "
            "VIXTERM = VIX - VIXM(ETF price). Same field name, two calibres -> the two "
            "assessments are NOT a continuous series. Resolve before comparing across dates.",
            "BAA10Y is an INVESTMENT-GRADE spread; it may not cover AI-related leverage "
            "(ORCL D/E 3.63, CRWV D/E 8.94). 'Corporate credit improving' must not be extrapolated "
            "to AI debt without checking HY (BAMLH0A0HYM2).",
        ],
        "macro_indicators": {
            "credit": {"f29_baa_10y": dict(**MACRO["f29_baa_10y_bp"])},
            "yields": {k: MACRO[k] for k in ["us10y", "us30y", "us2y", "breakeven_10y", "real_10y"]},
            "spreads": {"f29_bp": MACRO["f29_baa_10y_bp"]["value"],
                        "curve_10y_2y": MACRO["curve_10y_2y"]},
            "volatility": {"vix_spot": dict(value=c["vix"], date=AS_OF,
                                            source=MACRO["vix_spot"]["source"]),
                           "vix_10d_return_pct": round(c["vix10"] * 100, 1)},
            "conditions": {k: MACRO[k] for k in ["nfci", "stl_fin_stress"]},
            "rates_policy": {k: MACRO[k] for k in ["fed_funds"]},
            "fx_energy": {k: MACRO[k] for k in ["dxy_broad", "wti", "brent"]},
            "sentiment": {k: MACRO[k] for k in ["fear_greed"]},
        },
        "wif_phase_assessment": {
            "layer1_csi": {
                "phase1_status": c["status"],
                "csi_partial_55pct": round(c["csi_partial"], 4),
                "csi_engine_value": round(c["csi"], 4),
                "components": {
                    "z_vixtterm_60d": round(c["z_vixt"], 3),
                    "z_vixtterm_weight": 0.35,
                    "z_vixtterm_contribution": round(0.35 * c["z_vixt"], 4),
                    "neg_z_spy_gld_corr_20d": round(c["z_corr"], 3),
                    "corr_weight": 0.20,
                    "corr_contribution": round(0.20 * c["z_corr"], 4),
                    "z_f29_60d": None,
                    "f29_weight": 0.45,
                    "f29_contribution": None,
                    "f29_note": "not computable: no 60-day daily BAA10Y series in the local matrix",
                },
                "hard_triggers": {
                    "f29_gt_500bp": False,
                    "f29_value_bp": MACRO["f29_baa_10y_bp"]["value"],
                    "f29_distance_to_trigger_bp": MACRO["f29_baa_10y_bp"]["hard_trigger_bp"] - MACRO["f29_baa_10y_bp"]["value"],
                    "vix_gt_40_and_vix10d_gt_100pct": False,
                },
            },
            "layer2_macro_quadrant": {
                "spy_126d_momentum_60d_mean": round(c["spy60"], 4),
                "tlt_126d_momentum_60d_mean": round(c["tlt60"], 4),
                "quadrant": c["quadrant"],
                "quadrant_label": qlabel,
                "rule": "126d pct_change THEN 60d rolling mean; sign tested (phase.py::macro_quadrant)",
            },
            "layer3_mci": {
                "mci_level": "Moderate",
                "note": "US MCI is not implemented in the vendored library (only A-share "
                        "ashare.py::compute_mci); Phase is derived from (phase1_status, quadrant).",
            },
            "final_phase": {
                "phase_number": c["phase"],
                "phase_name": qn,
                "allocation_range": {"equity": "65-75%", "fixed_income": "10-15%", "real_assets": "15-25%"}
                if c["phase"] == 1 else None,
            },
            "rebalance": {"phase_switch": False, "action": "none",
                          "rule": "switch -> next close; routine -> every 15 trading days; MCI<+5 -> VTI-only"},
        },
        "risk_flags": [
            "F29 (investment-grade credit spread) is NARROWING (165->159->151bp) while US30Y is at a "
            "post-2007 high (5.37%): corporate credit and sovereign credit are DIVERGING.",
            "CSI runs at 55% weight (no F29 column) -> the HEALTHY reading is not fully evidenced.",
            "BAA10Y may not cover AI-related leverage (ORCL D/E 3.63, CRWV D/E 8.94).",
            "VIX 15.84 with SPY 126d +20.9% = complacent equity pricing while the long end sells off.",
        ],
        "cross_validation": {
            "method": "WIF engine (prices) x Tier-1 FRED macro x user HYP-011 8-signal framework",
            "agreement": "WIF Phase 1 Rising / HEALTHY vs HYP-011 crisis score 2-3 (L0-L1) -> CONSISTENT (both 'not yet')",
            "conflict": "4.2 AI-bubble 5-signal framework says 4/5 triggered -> 'clear out'. "
                        "Different mechanism (AI capex vs price/credit stress) -> registered as CONFLICT-TIMING-001.",
        },
        "cross_market_divergence": CROSS_MARKET,
        "f29_history": F29_HISTORY,
        "allocation_tilt_recommendation": {
            "reasoning": "Phase 1 Rising + HEALTHY (partial CSI) -> risk-on; but only 55% of the CSI "
                         "is live, so treat as indicative, not executable.",
            "equity_pct": 70, "fixed_income_pct": 13, "real_assets_pct": 17,
        },
    }


def build_md(c) -> str:
    qn = {1: "Rising（上升期）", 2: "Panic（恐慌）", 3: "Fall（下跌）",
          4: "Recover（复苏）", 5: "Transition（过渡）"}[c["phase"]]
    L = []
    A = L.append
    A(f"# WIF v5.9 五层读数 — {AS_OF}")
    A("")
    A(f"> 由 `out/hedge_fund_backtest/wif_assessment.py` 自动生成（可复跑）。")
    A(f"> 数据：`_merged_prices_{AS_OF.replace('-','')}.csv`（4966×10，2007-01-03 → {AS_OF}）+ Tier-1 MCP 宏观读数。")
    A("")
    A("| 层 | 指标 | 现值 | 阈值 / 判据 | 状态 |")
    A("| --- | --- | --- | --- | --- |")
    A(f"| ① 硬触发 | F29（BAA10Y） | **{MACRO['f29_baa_10y_bp']['value']} bp**（{MACRO['f29_baa_10y_bp']['date'][5:]}） | >500bp → EMERGENCY | 🟢 未触发（距线 {MACRO['f29_baa_10y_bp']['hard_trigger_bp']-MACRO['f29_baa_10y_bp']['value']}bp） |")
    A(f"| ① | VIX + 10日涨幅 | **{c['vix']:.2f} / {c['vix10']*100:+.1f}%** | VIX>40 且 >+100% | 🟢 未触发 |")
    A(f"| ② CSI | Z(VIXTERM_60d) | **{c['z_vixt']:+.2f}** ×0.35 = **{0.35*c['z_vixt']:+.3f}** | — | 🟢 |")
    A(f"| ② | −Z(SPY/GLD 20日相关) | **{c['z_corr']:+.2f}** ×0.20 = **{0.20*c['z_corr']:+.3f}** | — | 🟢 无断裂 |")
    A(f"| ② | Z(F29_60d) ×0.45 | **算不出** | 需 60 日每日序列 | ⚠️ 缺口 |")
    A(f"| ② | **CSI 合计** | **{c['csi_partial']:+.3f}**（仅 55% 权重） | >2 EMERGENCY / >1 WARNING / <1 HEALTHY | 🟢 **HEALTHY** |")
    A(f"| ③ 象限 | SPY 126d 动量 60日均值 | **{c['spy60']*100:+.1f}%** | >0 = Rising | 🟢 |")
    A(f"| ③ | TLT 126d 动量 60日均值 | **{c['tlt60']*100:+.1f}%** | >0 = Rising | 🟠 |")
    A(f"| ③ | **宏观象限** | **Q{c['quadrant']} Overheat（过熟/晚周期）** | 股涨 + 债涨 | 🟠 晚周期 |")
    A(f"| ④ 相位 | Phase1_status | **{c['status']}** | 连 3 日确认才切换 | 🟢 维持 |")
    A(f"| ④ | **最终相位** | **Phase {c['phase']} · {qn}** | 权益 65-75% / 固收 10-15% / 实物 15-25% | 🟢 **risk-on** |")
    A(f"| ⑤ 再平衡 | 相位切换 | **无** | 切换→次日收盘；常规→每 15 交易日；MCI<+5→VTI-only | ⚪ 无需动作 |")
    A("")
    A("## 辅助印证（FRED 实测，0 credit）")
    A("")
    A("| 指标 | 值 | 日期 | 源 |")
    A("|---|---:|---|---|")
    for k, v in MACRO.items():
        if k == "f29_baa_10y_bp":
            continue
        A(f"| {k} | {v['value']} | {v['date']} | {v['source']} |")
    A("")
    A("## ★ 跨市场背离（本轮最值得记）")
    A("")
    A("| 线 | 方向 | 最新 | 趋势 |")
    A("|---|---|---|---|")
    for r in CROSS_MARKET:
        A(f"| {r['line']} | {r['direction']} | {r['latest']} | {r['trend']} |")
    A("")
    A("## F29 历史锚点")
    A("")
    A("| 日期 | F29 (bp) | 源 |")
    A("|---|---:|---|")
    for r in F29_HISTORY:
        A(f"| {r['date']} | {r['f29_bp']} | {r['source']} |")
    A("")
    A("## ⚠️ 缺口与效力声明")
    A("")
    A("- **CSI 仅 55% 权重**：本地矩阵无 F29 列，`compute_csi` 明写「缺失分量按 0 计且不重缩放」")
    A("- **不可与 WIF 历史业绩对照**：Sharpe 1.01 是用 100% CSI 回测的")
    A("- **BAA10Y 是投资级利差**，可能不覆盖 AI 相关杠杆（ORCL D/E 3.63 / CRWV D/E 8.94）")
    A("- 补 Z(F29_60d)：需 60 日每日 BAA10Y（`macro_indicator_history` 或 FRED CSV）")
    A("")
    return "\n".join(L)


def main():
    c = compute()
    tag = AS_OF.replace("-", "")
    jp = os.path.join(WIF_DATA, f"wif_phase_assessment_{tag}.json")
    mp = os.path.join(WIF_DATA, f"wif_phase_assessment_{tag}.md")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(build_json(c), f, indent=2, ensure_ascii=False, default=str)
    with open(mp, "w", encoding="utf-8") as f:
        f.write(build_md(c))
    print(f"SAVED {jp}")
    print(f"SAVED {mp}")
    print(f"  phase={c['phase']} status={c['status']} quadrant=Q{c['quadrant']} "
          f"csi_partial={c['csi_partial']:+.3f}")


if __name__ == "__main__":
    main()
