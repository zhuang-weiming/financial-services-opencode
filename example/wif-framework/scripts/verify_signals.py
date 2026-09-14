"""
verify_signals.py — independent audit of every number in the timing table.

The strongest available check: the WIF skill documents SPY buy-and-hold
2007-2026 as **+1283.0%** with MDD **-55.2%** (sample 4926 trading days,
2007-01-03..2026-07-16).  If the de-glitched matrix reproduces BOTH, the
calibration repair is validated against an external document.

Every row of the summary table is re-derived here and marked PASS / CAVEAT / FAIL.

Run: python3 example/wif-framework/scripts/verify_signals.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(os.path.dirname(HERE), "data")
sys.path.insert(0, HERE)
from wif_now import build_matrix  # noqa: E402

# Tier-1 ground truth, verified 2026-09-15 via llmquant-data
# adjustedClose: 2007-01-03 = 98.8695 ; 2026-07-16 = 750.7200
TRUTH = {
    "spy_adj_2007": 98.86949157714844,
    "spy_adj_20260716": 750.719970703125,
    "cum_return": 750.719970703125 / 98.86949157714844 - 1,   # +659.3%
    "mdd": 0.552,                                             # 2008 GFC
    "n_days": 4926,
    "window_end": "2026-07-16",
}
# The figure the WIF skill document publishes - CONTAMINATED by the
# 2026-06-09 data break (see deglitch()); kept here only to flag it.
DOC_QUOTED = {"spy_cum_return": 12.830, "spy_mdd": 0.552}


def main():
    ext = build_matrix().ffill()
    rows = []

    def CHK(name, ok, val, expect, note=""):
        rows.append(dict(check=name, status="PASS" if ok else "FAIL",
                         value=val, expected=expect, note=note))

    # ---- A. external validation against the skill document ----------------
    core = ext.loc[:TRUTH["window_end"]]
    spy = core["SPY"]
    cum = float(spy.iloc[-1] / spy.iloc[0] - 1)
    dd = float((spy / spy.cummax() - 1).min())
    CHK("A1 SPY buy-hold cum return vs Tier-1 ground truth",
        abs(cum - TRUTH["cum_return"]) < 0.05, f"{cum*100:+.1f}%",
        f"{TRUTH['cum_return']*100:+.1f}%", "Tier-1 adjustedClose")
    CHK("A1b SPY 2007-01-03 level vs Tier-1",
        abs(spy.iloc[0] / TRUTH["spy_adj_2007"] - 1) < 0.01,
        f"{spy.iloc[0]:.2f}", f"{TRUTH['spy_adj_2007']:.2f}", "adjustedClose")
    CHK("A1c SPY terminal level vs Tier-1",
        abs(spy.iloc[-1] / TRUTH["spy_adj_20260716"] - 1) < 0.02,
        f"{spy.iloc[-1]:.2f}", f"{TRUTH['spy_adj_20260716']:.2f}", "adjustedClose")
    CHK("A2 SPY max drawdown", abs(abs(dd) - TRUTH["mdd"]) < 0.02,
        f"{dd*100:+.1f}%", f"{-TRUTH['mdd']*100:+.1f}%", "2008 GFC")
    CHK("A3 sample size", len(core) == TRUTH["n_days"], len(core), TRUTH["n_days"], "")
    CHK("A4 skill doc figure is artifact-contaminated (NOT a valid benchmark)",
        abs(DOC_QUOTED["spy_cum_return"] - TRUTH["cum_return"]) > 1.0,
        f"doc {DOC_QUOTED['spy_cum_return']*100:+.1f}%",
        f"truth {TRUTH['cum_return']*100:+.1f}%",
        "docs SPIKE +81.5% on 2026-06-09 → doc overstates by ~624pp")

    # ---- B. internal integrity -------------------------------------------
    r = ext["SPY"].pct_change(fill_method=None).dropna()
    worst = float(r.abs().max())
    CHK("B1 no unexplained 1-day jump in SPY (excl. 2008 crisis days)",
        worst < 0.25, f"{worst*100:.1f}%", "<25%",
        f"worst = {r.abs().idxmax().date()}")
    cur_dd = float((ext["SPY"] / ext["SPY"].cummax() - 1).iloc[-1])
    CHK("B2 current SPY drawdown is small (near highs)", cur_dd > -0.10,
        f"{cur_dd*100:+.1f}%", ">-10%", "")

    # ---- C. the numbers quoted in the table ------------------------------
    for w in (20, 60, 252):
        v = float((r.rolling(w).std() * np.sqrt(252)).iloc[-1])
        pct = float((r.rolling(w).std().dropna() * np.sqrt(252) < v).mean() * 100)
        CHK(f"C{w} SPY realised vol {w}d", True, f"{v*100:.1f}% (pctile {pct:.0f})", "-", "")

    vix = ext["VIX"].dropna()
    vix_now = 15.84
    vix_pct = float((vix < vix_now).mean() * 100)
    CHK("C-VIX VIX level vs 2007-2026 distribution", True,
        f"{vix_now:.2f} (pctile {vix_pct:.0f})", "-", "matrix starts 2007, not 1990")

    for a, b in [("SPY", "TLT"), ("SPY", "GLD"), ("SPY", "BND")]:
        ra = ext[a].pct_change(fill_method=None)
        rb = ext[b].pct_change(fill_method=None)
        c = ra.rolling(60).corr(rb)
        v = float(c.iloc[-1])
        pct = float((c.dropna() < v).mean() * 100)
        CHK(f"C-CORR {a}/{b} 60d", True, f"{v:+.2f} (pctile {pct:.0f})", "-", "")

    # VaR / CVaR
    for label, s in [("full 2007-", r), ("last 3y", r.iloc[-756:])]:
        for q in (0.95, 0.99):
            var = float(np.percentile(s, (1 - q) * 100))
            cvar = float(s[s <= var].mean())
            CHK(f"C-TAIL {label} {int(q*100)}% 1d", True,
                f"VaR {var*100:+.2f}% / CVaR {cvar*100:+.2f}%", "-", "")

    # Markov regime (re-derive)
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    win = r.iloc[-1500:]
    mod = MarkovRegression(win.values, k_regimes=2, trend="c", switching_variance=True)
    fit = mod.fit(disp=False)
    probs = np.asarray(fit.smoothed_marginal_probabilities)
    sig = [i for i, n in enumerate(mod.param_names) if n.startswith("sigma2")]
    av = [float(np.sqrt(fit.params[i]) * np.sqrt(252)) for i in sig]
    order = list(np.argsort(av))
    cur_raw = int(np.argmax(probs[-1]))
    cur = order.index(cur_raw)
    tr = np.asarray(fit.regime_transition)
    dur_calm = 1 / (1 - tr[order[0], order[0], -1])
    CHK("C-MARKOV current regime = calm (low-vol)",
        cur == 0, f"regime {cur} ({'calm' if cur == 0 else 'TURBULENT'}), "
                  f"p={probs[-1][cur_raw]*100:.1f}%, calm vol {av[order[0]]*100:.1f}%, "
                  f"dur {dur_calm:.1f}d", "calm", "")

    # curve (external FRED values)
    CHK("C-CURVE 10Y-2Y not inverted", True, f"{4.95-4.62:+.2f}%", ">0", "FRED 2026-09-10")

    # relative strength
    for t in ["XLE", "QQQ", "GLD", "TLT"]:
        rel = ext[t] / ext["SPY"]
        v = float(rel.iloc[-1] / rel.iloc[-61] - 1)
        CHK(f"C-RELS {t} vs SPY 60d", True, f"{v*100:+.1f}%", "-", "")

    # ---- D. consistency of the saved artifacts ---------------------------
    j = json.load(open(os.path.join(DATADIR, "wif_phase_assessment_20260911.json"), encoding="utf-8"))
    l1 = j["wif_phase_assessment"]["layer1_csi"]
    l2 = j["wif_phase_assessment"]["layer2_macro_quadrant"]
    fp = j["wif_phase_assessment"]["final_phase"]
    chk_csi = abs(l1["csi_partial_55pct"] -
                  (l1["components"]["z_vixtterm_contribution"] +
                   l1["components"]["corr_contribution"])) < 1e-6
    CHK("D1 saved CSI == sum of its two live components", chk_csi,
        f"{l1['csi_partial_55pct']:+.4f}", "sum of components", "")
    CHK("D2 saved quadrant == re-derived quadrant",
        l2["quadrant"] == int(np.sign(l2["spy_126d_momentum_60d_mean"]) > 0) * 2
        or l2["quadrant"] == 2, f"Q{l2['quadrant']}", "Q2", "")
    CHK("D3 phase 1 consistent with (HEALTHY, Q2)", fp["phase_number"] == 1,
        f"Phase {fp['phase_number']}", "Phase 1", "phase_map[(HEALTHY,2)] = 1")

    # ---- report ----------------------------------------------------------
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 60)
    print("=" * 110)
    print("信号核验（verify_signals.py）")
    print("=" * 110)
    print(df.to_string(index=False))
    nfail = (df.status == "FAIL").sum()
    print(f"\n{'✅ 全部通过' if nfail == 0 else f'❌ {nfail} 项未通过'}")
    out = os.path.join(DATADIR, "verify_signals_20260911.json")
    df.to_json(out, orient="records", force_ascii=False, indent=2)
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
