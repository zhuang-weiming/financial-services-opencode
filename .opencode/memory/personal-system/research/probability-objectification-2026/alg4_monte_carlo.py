"""Probability-Objectification Algorithm 4: Monte Carlo Uncertainty Layer.

ROLE: Not a 4th point-estimate algorithm — a ROBUSTNESS / UNCERTAINTY layer
wrapping Algorithms 1-3. It answers the question the first three cannot:
"how sensitive are the 16.3/29.0/15.4/39.3 outputs to the inputs we had to
assume?" (single-point WTI/FFR/CPI values, subjective 5-signal probabilities,
Bayesian priors, and the Alg3 anchor->scenario mapping matrix flagged in the
5-Why adversarial review as the most fragile component).

METHOD:
  For N iterations:
    1. Sample perturbed inputs from documented distributions (each parameter's
       uncertainty is a MODEL CHOICE, documented below):
         wti_now       ~ N(82.55, 4.0),  clipped [60, 110]
         ffr_now       ~ N(3.63, 0.25),  clipped [2.5, 5.5]
         china_cpi_now ~ N(0.5, 0.30),   clipped [-0.5, 2.5]
         5 signal probs ~ each clipped-N(p, 0.08) in [0.05, 0.98]
         priors        ~ Dirichlet with params  [30, 30, 15, 25] (small noise)
         Alg3 anchor->scenario matrix ~ each contribution jittered
    2. Re-run Alg1 (signal scoring), Alg2 (Bayesian), Alg3 (similarity)
       with the perturbed inputs — implementations copied from the originals
       but parameterized; base-case output is verified against the originals'
       JSON so the MC wrapper does not change the deterministic math.
    3. Record each algorithm's probabilities + the 3-method ensemble mean.
  Output:
    per-scenario mean / median / 95% credible interval for each algorithm
    and for the ensemble; stability of scenario ranking; % of iterations
    where D is the top scenario.

NOT FORWARD-LOOKING PREDICTION: this quantifies parameter uncertainty only,
it does not telescope out regime-change risk (which stays in §5.8) nor model
risk (e.g. wrong fuzzy thresholds). See report §5.3.1 honest-boundary list.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent

N_ITER = 3000
SEED = 20260817
rng = np.random.default_rng(SEED)

SCEN = ["A_old_inflation", "B_ai_solution", "C_stagflation_loss", "D_deflation_bust"]
SHORT = {"A_old_inflation": "A", "B_ai_solution": "B", "C_stagflation_loss": "C", "D_deflation_bust": "D"}

# --------------------------------------------------------------------------
# Shared fuzzy helpers (identical to alg1/alg2)
# --------------------------------------------------------------------------
def _trap(x, lo, hi):
    if x <= lo:
        return 0.0
    if x >= hi:
        return 1.0
    return (x - lo) / (hi - lo)


def _trap_rev(x, lo, hi):
    return 1.0 - _trap(x, lo, hi)


def _trap_band(x, lo_a, lo_b, hi_b, hi_a):
    rise = _trap(x, lo_a, lo_b)
    fall = 1 - _trap(x, hi_b, hi_a)
    return max(0.0, min(rise, fall))


def clipn(x, lo, hi):
    return float(np.clip(x, lo, hi))


# --------------------------------------------------------------------------
# Algorithm 1 as a function (parameterized; base == alg1_original)
# --------------------------------------------------------------------------
def alg1_probs(sig, wti, ffr, ccpi):
    """Returns {scenario: prob} using the exact alg1 logic."""
    bust = min(0.95, 0.60 * sig["capex_rev"] + 0.25 * sig["leverage"] + 0.15 * sig["focus_shift"])
    productivity = 1 - bust
    partial = sig["focus_shift"] * (1 - sig["capex_rev"])

    states = {
        "x1_bust": bust,
        "x1_productivity": productivity,
        "x1_partial": partial,
        "x2_escalation_100": _trap(wti, 95, 110),
        "x2_extreme_150": _trap(wti, 135, 165),
        "x2_flat_75_95": _trap_band(wti, 70, 75, 95, 100),
        "x2_de-escalation": _trap_rev(wti, 55, 70),
        "x3_violent": _trap(ffr, 5.5, 6.0),
        "x3_slow": _trap_band(ffr, 3.4, 3.5, 4.5, 4.6),
        "x3_surrender": _trap_rev(ffr, 2.0, 2.8),
        "x3_lost_credibility": 0.5 * (1 - _trap(ffr, 5.5, 6.0)) + 0.35 * sig["gov_response"],
        "x4_soft_1_2": _trap_band(ccpi, 0.7, 1.0, 2.0, 2.3),
        "x4_crisis": _trap(ccpi, 0.2, 0.5) * 0.8 + 0.2 * sig["rate_credit"],
    }
    reqs = {
        "A_old_inflation": (["x1_bust", "x2_escalation_100", "x3_violent", "x4_soft_1_2"], [0.35, 0.25, 0.25, 0.15]),
        "B_ai_solution": (["x1_productivity", "x2_flat_75_95", "x3_slow", "x4_soft_1_2"], [0.40, 0.20, 0.20, 0.20]),
        "C_stagflation_loss": (["x2_extreme_150", "x3_lost_credibility", "x1_partial", "x4_soft_1_2"], [0.35, 0.30, 0.20, 0.15]),
        "D_deflation_bust": (["x1_bust", "x2_de-escalation", "x3_surrender", "x4_crisis"], [0.35, 0.20, 0.20, 0.25]),
    }
    scores = {}
    for scen, (ss, ws) in reqs.items():
        scores[scen] = sum(w * states[s] for s, w in zip(ss, ws))
    tot = sum(scores.values())
    return {k: v / tot for k, v in scores.items()}


# --------------------------------------------------------------------------
# Algorithm 2 as a function (parameterized; base == alg2_original)
# --------------------------------------------------------------------------
def alg2_probs(sig, wti, ffr, ccpi, priors):
    bust = min(0.95, 0.60 * sig["capex_rev"] + 0.25 * sig["leverage"] + 0.15 * sig["focus_shift"])
    E = {
        "x1_bust": bust,
        "x1_productivity": 1 - bust,
        "x1_partial": sig["focus_shift"] * (1 - sig["capex_rev"]),
        "x2_de_escalation": _trap_rev(wti, 55, 70),
        "x2_flat_75_95": _trap_band(wti, 70, 75, 95, 100),
        "x2_escalation_100": _trap(wti, 95, 110),
        "x2_extreme_150": _trap(wti, 135, 165),
        "x3_surrender": _trap_rev(ffr, 2.0, 2.8),
        "x3_slow": _trap_band(ffr, 3.4, 3.5, 4.5, 4.6),
        "x3_violent": _trap(ffr, 5.5, 6.0),
        "x3_lost_credibility": 0.5 * (1 - _trap(ffr, 5.5, 6.0)) + 0.35 * sig["gov_response"],
        "x4_soft_1_2": _trap_band(ccpi, 0.7, 1.0, 2.0, 2.3),
        "x4_crisis": _trap(ccpi, 0.2, 0.5) * 0.8 + 0.2 * sig["rate_credit"],
    }
    E_soft = {k: 0.075 + 0.85 * v for k, v in E.items()}
    groups = {
        "x1": ["x1_bust", "x1_productivity", "x1_partial"],
        "x2": ["x2_de_escalation", "x2_flat_75_95", "x2_escalation_100", "x2_extreme_150"],
        "x3": ["x3_surrender", "x3_slow", "x3_violent", "x3_lost_credibility"],
        "x4": ["x4_soft_1_2", "x4_crisis"],
    }
    GW = {"x1": 0.30, "x2": 0.25, "x3": 0.25, "x4": 0.20}
    M = {
        "A_old_inflation": [("x1_bust", 1), ("x1_productivity", 0), ("x2_escalation_100", 1), ("x2_flat_75_95", 0), ("x2_de_escalation", 0), ("x3_violent", 1), ("x3_surrender", 0), ("x3_slow", 0), ("x4_soft_1_2", 1), ("x4_crisis", 0)],
        "B_ai_solution": [("x1_productivity", 1), ("x1_bust", 0), ("x2_flat_75_95", 1), ("x2_escalation_100", 0), ("x2_extreme_150", 0), ("x3_slow", 1), ("x3_violent", 0), ("x3_surrender", 0), ("x4_soft_1_2", 1), ("x4_crisis", 0)],
        "C_stagflation_loss": [("x2_extreme_150", 1), ("x2_flat_75_95", 0), ("x2_de_escalation", 0), ("x3_lost_credibility", 1), ("x3_violent", 0), ("x1_partial", 1), ("x1_productivity", 0), ("x4_soft_1_2", 1), ("x4_crisis", 0)],
        "D_deflation_bust": [("x1_bust", 1), ("x1_productivity", 0), ("x2_de_escalation", 1), ("x2_escalation_100", 0), ("x2_extreme_150", 0), ("x3_surrender", 1), ("x3_violent", 0), ("x3_slow", 0), ("x4_crisis", 1), ("x4_soft_1_2", 0)],
    }
    logL = {}
    for scen, evs in M.items():
        gl = {g: 0.0 for g in groups}
        gc = {g: 0 for g in groups}
        for key, expected in evs:
            g = next(gg for gg, ks in groups.items() if key in ks)
            p = E_soft[key]
            gl[g] += math.log(p) if expected else math.log(1 - p)
            gc[g] += 1
        logL[scen] = sum(GW[g] * (gl[g] / gc[g]) for g in groups if gc[g])
    un = {s: priors[s] * math.exp(l) for s, l in logL.items()}
    tot = sum(un.values())
    return {s: v / tot for s, v in un.items()}


# --------------------------------------------------------------------------
# Algorithm 3 as a function (parameterized; base == alg3_original)
# --------------------------------------------------------------------------
def alg3_probs(current_vals, anchors, matrix_jitter_seed):
    """Recompute alg3 with per-iteration jitter on the anchor->scenario matrix.
    current_vals: dict feature->value for the current snapshot
    anchors: DataFrame(index=anchor, columns=features)
    matrix: kept module-level but jittered per iteration.
    """
    # build current row
    cur_df = {k: current_vals[k] for k in FEATURES}
    rows = list(anchors.index) + ["2026_current"]
    data = {}
    for a in anchors.index:
        data[a] = {f: anchors.loc[a, f] for f in FEATURES}
    data["2026_current"] = cur_df

    comb_z = {}
    for f in FEATURES:
        vals = np.array([data[r][f] for r in rows], dtype=float)
        ok = ~np.isnan(vals)
        if ok.sum() == 0:
            continue
        mu = vals[ok].mean()
        sd = vals[ok].std()
        sd = sd if sd > 1e-12 else 1.0
        comb_z[f] = {r: (data[r][f] - mu) / sd if not np.isnan(data[r][f]) else np.nan for r in rows}

    distances = {}
    overlap = {}
    for a in anchors.index:
        feats = [f for f in FEATURES if not np.isnan(comb_z[f][a]) and not np.isnan(comb_z[f]["2026_current"])]
        if not feats:
            distances[a] = np.nan
            overlap[a] = 0
            continue
        d = math.sqrt(sum((comb_z[f][a] - comb_z[f]["2026_current"]) ** 2 for f in feats))
        distances[a] = d
        overlap[a] = len(feats)

    sim = {a: 1.0 / (1.0 + d) for a, d in distances.items() if d == d}
    max_feat = max(overlap.values()) if overlap else 1
    rel = {a: overlap[a] / max_feat for a in anchors.index}
    sim_w = {a: sim[a] * rel[a] for a in sim}
    tot_w = sum(sim_w.values())
    sim_norm = {a: v / tot_w for a, v in sim_w.items()}

    # jitter the mapping matrix (the 5-Why-flagged fragile component)
    matrix = {}
    for a, mapping in ANCHOR_SCENARIO.items():
        keys = list(mapping.keys())
        vals = np.array([mapping[k] for k in keys])
        jitter = rng.normal(0.0, 0.06, size=vals.shape)
        jv = np.clip(vals + jitter, 0.05, 0.95)
        jv = jv / jv.sum()
        matrix[a] = dict(zip(keys, jv))

    scen_score = {s: 0.0 for s in SCEN}
    for a, w in sim_norm.items():
        for s, c in matrix[a].items():
            scen_score[s] += w * c
    tot = sum(scen_score.values())
    return {s: v / tot for s, v in scen_score.items()}


# --------------------------------------------------------------------------
# Module-level constants for alg3 (same as original)
# --------------------------------------------------------------------------
FEATURES = ["cpi_yoy_pct", "gs10_pct", "ffr_pct", "real10_pct", "wti_usd", "credit_bp", "gold_usd"]
ANCHOR_SCENARIO = {
    "1971.8_nixon": {"A_old_inflation": 0.55, "C_stagflation_loss": 0.35, "B_ai_solution": 0.10},
    "2000.3_dotcom": {"D_deflation_bust": 0.90, "B_ai_solution": 0.10},
    "2007.10_gfc": {"D_deflation_bust": 0.90, "B_ai_solution": 0.10},
    "2021-23_mini": {"C_stagflation_loss": 0.60, "B_ai_solution": 0.40},
}

# Base (unperturbed) inputs — must reproduce the original JSONs exactly
BASE_SIG = {"capex_rev": 0.85, "leverage": 0.70, "focus_shift": 0.50, "rate_credit": 0.60, "gov_response": 0.30}
BASE_WTI, BASE_FFR, BASE_CCPI = 82.55, 3.63, 0.5
BASE_PRIORS = {"A_old_inflation": 0.30, "B_ai_solution": 0.30, "C_stagflation_loss": 0.15, "D_deflation_bust": 0.25}


def sample_inputs():
    """Draw one Monte Carlo iteration's perturbed inputs."""
    # Real-variable uncertainty: WTI ±4 (oil monthly vol), FFR ±25bp (path
    # uncertainty), China CPI ±0.3pp (monthly noise/rounding).
    wti = clipn(rng.normal(BASE_WTI, 4.0), 60, 110)
    ffr = clipn(rng.normal(BASE_FFR, 0.25), 2.5, 5.5)
    ccpi = clipn(rng.normal(BASE_CCPI, 0.30), -0.5, 2.5)
    # 5-signal probabilities: each is itself an estimate ±0.08
    sig = {k: clipn(rng.normal(v, 0.08), 0.05, 0.98) for k, v in BASE_SIG.items()}
    # Prior jitter: Dirichlet around (30,30,15,25)
    pri = rng.dirichlet(np.array([30, 30, 15, 25]) * 1.0)
    priors = dict(zip(SCEN, pri))
    return sig, wti, ffr, ccpi, priors


def verify_base() -> bool:
    """Spot check: with base inputs, alg1/alg2 must match the original JSONs."""
    p1 = alg1_probs(BASE_SIG, BASE_WTI, BASE_FFR, BASE_CCPI)
    p2 = alg2_probs(BASE_SIG, BASE_WTI, BASE_FFR, BASE_CCPI, BASE_PRIORS)
    r1 = json.loads((OUT / "alg1_signal_scoring.json").read_text())["probabilities"]
    r2 = json.loads((OUT / "alg2_bayesian_update.json").read_text())["posteriors"]
    ok1 = all(abs(p1[k] - r1[k]) < 1e-3 for k in SCEN)
    ok2 = all(abs(p2[k] - r2[k]) < 1e-3 for k in SCEN)
    print(f"base-check alg1: {'OK' if ok1 else 'MISMATCH'}")
    print(f"base-check alg2: {'OK' if ok2 else 'MISMATCH'}")
    return ok1 and ok2


def main() -> None:
    import pandas as pd

    if not verify_base():
        raise SystemExit("Base-case mismatch with original algorithms — abort.")

    anchors = pd.read_csv(OUT / "anchor_features.csv", index_col=0)
    current_row = pd.read_csv(OUT / "current_snapshot.csv", index_col=0).iloc[0]
    current_vals = {f: current_row[f] for f in FEATURES}

    rec = {alg: {s: [] for s in SCEN} for alg in ["alg1", "alg2", "alg3", "ensemble"]}

    for it in range(N_ITER):
        sig, wti, ffr, ccpi, priors = sample_inputs()
        p1 = alg1_probs(sig, wti, ffr, ccpi)
        p2 = alg2_probs(sig, wti, ffr, ccpi, priors)
        p3 = alg3_probs(current_vals, anchors, it)
        for s in SCEN:
            rec["alg1"][s].append(p1[s])
            rec["alg2"][s].append(p2[s])
            rec["alg3"][s].append(p3[s])
            rec["ensemble"][s].append((p1[s] + p2[s] + p3[s]) / 3.0)

    # ---- Summary statistics ----
    out = {"algorithm": "alg4_monte_carlo", "n_iter": N_ITER, "seed": SEED, "scenarios": {}}
    labels = {"A_old_inflation": "A 老剧本", "B_ai_solution": "B AI 化解", "C_stagflation_loss": "C 滞胀失控", "D_deflation_bust": "D 通缩破裂"}

    print(f"=== ALGORITHM 4: MONTE CARLO UNCERTAINTY LAYER ({N_ITER} iters, seed {SEED}) ===")
    for s in SCEN:
        out["scenarios"][s] = {"label": labels[s]}
        for alg in ["alg1", "alg2", "alg3", "ensemble"]:
            arr = np.array(rec[alg][s])
            mean = arr.mean()
            lo, med, hi = np.percentile(arr, [2.5, 50, 97.5])
            out["scenarios"][s][alg] = {"mean": round(float(mean), 3), "median": round(float(med), 3), "lo95": round(float(lo), 3), "hi95": round(float(hi), 3)}
        ens_lo = out["scenarios"][s]["ensemble"]["lo95"]
        ens_hi = out["scenarios"][s]["ensemble"]["hi95"]
        print(f"  {labels[s]:<12}  ensemble 95% CI: {ens_lo*100:5.1f}% - {ens_hi*100:5.1f}%   (median {out['scenarios'][s]['ensemble']['median']*100:.1f}%)")

    # ---- Ranking stability: how often is each scenario the top ensemble pick? ----
    top_counts = {s: 0 for s in SCEN}
    for i in range(N_ITER):
        ens_i = {s: rec["ensemble"][s][i] for s in SCEN}
        top = max(ens_i.items(), key=lambda kv: kv[1])[0]
        top_counts[top] += 1
    out["ranking_stability"] = {s: round(top_counts[s] / N_ITER, 3) for s in SCEN}

    # ---- Key question: is 'D top' robust? ---- 
    d_over_b = sum(1 for i in range(N_ITER) if rec["ensemble"]["D_deflation_bust"][i] > rec["ensemble"]["B_ai_solution"][i]) / N_ITER
    out["d_over_b_frequency"] = round(d_over_b, 3)
    a_above_25 = sum(1 for i in range(N_ITER) if rec["ensemble"]["A_old_inflation"][i] > 0.25) / N_ITER
    out["A_above_25pct_frequency"] = round(a_above_25, 3)
    d_above_40 = sum(1 for i in range(N_ITER) if rec["ensemble"]["D_deflation_bust"][i] > 0.40) / N_ITER
    out["D_above_40pct_frequency"] = round(d_above_40, 3)

    print("\n=== RANKING STABILITY (top scenario by ensemble) ===")
    for s in SCEN:
        print(f"  {labels[s]:<12} top in {top_counts[s]/N_ITER*100:5.1f}% of iterations")
    print(f"\n  P(D > B): {d_over_b:.1%}")
    print(f"  P(A > 25%): {a_above_25:.1%}   (was 30% subjective)")
    print(f"  P(D > 40%): {d_above_40:.1%}   (was 25% subjective)")

    # Parameter record (documented uncertainty choices)
    out["uncertainty_parameters"] = {
        "wti": "N(82.55, 4.0) clipped [60,110]",
        "ffr": "N(3.63, 0.25) clipped [2.5,5.5]",
        "china_cpi": "N(0.5, 0.30) clipped [-0.5,2.5]",
        "signals": "each clipped-N(p, 0.08) in [0.05,0.98]",
        "priors": "Dirichlet((30,30,15,25))",
        "alg3_matrix": "each contribution + N(0, 0.06), clipped [0.05,0.95], renormalized",
        "note": "Uncertainty sigma choices are analyst-selected; see report honest-boundary. MC quantifies parameter uncertainty only, not regime-change or model risk.",
    }
    with (OUT / "alg4_monte_carlo.json").open("w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSaved alg4_monte_carlo.json")


if __name__ == "__main__":
    main()