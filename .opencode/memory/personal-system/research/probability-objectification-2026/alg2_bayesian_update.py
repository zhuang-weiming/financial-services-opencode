"""Probability-Objectification Algorithm 2: Bayesian Updating.

Goal: start from the report's subjective priors (30/30/15/25) and use REAL
market data as evidence to compute posterior scenario probabilities.

Method:
    P(scenario | evidence) ∝ P(evidence | scenario) * P_prior(scenario)

Evidence = the state probabilities derived from real data in Algorithm 1:
    X1 bust/productivity/partial   (from 4.2 five-signal probabilities)
    X2 WTI states                   (from actual WTI 82.55 vs scenario bands)
    X3 FFR states                   (from actual FFR 3.63 vs scenario bands)
    X4 China CPI states             (from actual China CPI 0.5%)

Likelihood construction:
    For each scenario S with required states {r1..rk} (report §5.3):
        L(S) = Π_{required} P(state)  ×  Π_{opposite} (1 - P(state))
    where 'opposite' = the states that would contradict S (e.g. B expects
    WTI in band -> observing de-escalation or escalation lowers L(B)).

    We take the log, weight evidence by informativeness (each variable one
    data source), then renormalize with priors.

Note: scenario D and B share requirement structure partially; the Bayesian
product naturally handles that (shared evidence does not double-count when
normalizing across mutually exclusive scenarios).

Data (real, from report §5.1 + 4.2):
    WTI 82.55, FFR 3.63%, China CPI 0.5%, 5-signal probs.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent

# ---- Priors from report §5.3 (subjective starting point) ----
priors = {
    "A_old_inflation": 0.30,
    "B_ai_solution": 0.30,
    "C_stagflation_loss": 0.15,
    "D_deflation_bust": 0.25,
}

# ---- Evidence: reuse Algorithm 1 state probabilities (real data driven) ----
# (recompute here so script is self-contained; inputs identical to alg1)
signal_probabilities = {
    "capex_rev": 0.85, "leverage": 0.70, "focus_shift": 0.50,
    "rate_credit": 0.60, "gov_response": 0.30,
}
wti_now = 82.55
ffr_now = 3.63
china_cpi_now = 0.5


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


X1_bust = min(0.95, 0.60 * signal_probabilities["capex_rev"] + 0.25 * signal_probabilities["leverage"] + 0.15 * signal_probabilities["focus_shift"])
X1_productivity = 1 - X1_bust
X1_partial = signal_probabilities["focus_shift"] * (1 - signal_probabilities["capex_rev"])

E = {
    # evidence states with probabilities (derived from real data)
    "x1_bust": X1_bust,
    "x1_productivity": X1_productivity,
    "x1_partial": X1_partial,
    "x2_de_escalation": _trap_rev(wti_now, 55, 70),
    "x2_flat_75_95": _trap_band(wti_now, 70, 75, 95, 100),
    "x2_escalation_100": _trap(wti_now, 95, 110),
    "x2_extreme_150": _trap(wti_now, 135, 165),
    "x3_surrender": _trap_rev(ffr_now, 2.0, 2.8),
    "x3_slow": _trap_band(ffr_now, 3.4, 3.5, 4.5, 4.6),
    "x3_violent": _trap(ffr_now, 5.5, 6.0),
    "x3_lost_credibility": 0.5 * (1 - _trap(ffr_now, 5.5, 6.0)) + 0.35 * signal_probabilities["gov_response"],
    "x4_soft_1_2": _trap_band(china_cpi_now, 0.7, 1.0, 2.0, 2.3),
    "x4_crisis": _trap(china_cpi_now, 0.2, 0.5) * 0.8 + 0.2 * signal_probabilities["rate_credit"],
}

# ---- Likelihood maps: which evidence states each scenario expects (report §5.3) ----
# Each scenario = list of (evidence_key, expected) where expected=True means
# scenario requires this state, expected=False means scenario is inconsistent
# with it (observing it lowers likelihood).
scenario_evidence = {
    "A_old_inflation": [
        ("x1_bust", True), ("x1_productivity", False),
        ("x2_escalation_100", True), ("x2_flat_75_95", False), ("x2_de_escalation", False),
        ("x3_violent", True), ("x3_surrender", False), ("x3_slow", False),
        ("x4_soft_1_2", True), ("x4_crisis", False),
    ],
    "B_ai_solution": [
        ("x1_productivity", True), ("x1_bust", False),
        ("x2_flat_75_95", True), ("x2_escalation_100", False), ("x2_extreme_150", False),
        ("x3_slow", True), ("x3_violent", False), ("x3_surrender", False),
        ("x4_soft_1_2", True), ("x4_crisis", False),
    ],
    "C_stagflation_loss": [
        ("x2_extreme_150", True), ("x2_flat_75_95", False), ("x2_de_escalation", False),
        ("x3_lost_credibility", True), ("x3_violent", False),
        ("x1_partial", True), ("x1_productivity", False),
        ("x4_soft_1_2", True), ("x4_crisis", False),
    ],
    "D_deflation_bust": [
        ("x1_bust", True), ("x1_productivity", False),
        ("x2_de_escalation", True), ("x2_escalation_100", False), ("x2_extreme_150", False),
        ("x3_surrender", True), ("x3_violent", False), ("x3_slow", False),
        ("x4_crisis", True), ("x4_soft_1_2", False),
    ],
}

# ---- Evidence shrinkage: soften 0/1 memberships (avoid over-confidence) ----
# p_soft = 0.075 + 0.85*p  =>  p in [0,1] maps to [0.075, 0.925]
# This prevents a single near-certain signal from zeroing out a scenario.
SHRINK = lambda p: 0.075 + 0.85 * p
E_soft = {k: SHRINK(v) for k, v in E.items()}

# ---- Group weights: X1..X4 each contribute equally (macros are correlated;
# group-averaging avoids double-punishing a scenario for one macro cluster) ----
# evidence_key -> group
groups = {
    "x1": ["x1_bust", "x1_productivity", "x1_partial"],
    "x2": ["x2_de_escalation", "x2_flat_75_95", "x2_escalation_100", "x2_extreme_150"],
    "x3": ["x3_surrender", "x3_slow", "x3_violent", "x3_lost_credibility"],
    "x4": ["x4_soft_1_2", "x4_crisis"],
}
GROUP_WEIGHTS = {"x1": 0.30, "x2": 0.25, "x3": 0.25, "x4": 0.20}


# ---- Compute posterior (group-averaged log-likelihood) ----
log_likelihoods = {}
for scen, evs in scenario_evidence.items():
    # accumulate per-group log-likelihood
    group_logL = {g: 0.0 for g in groups}
    group_cnt = {g: 0 for g in groups}
    for key, expected in evs:
        g = next(gg for gg, keys in groups.items() if key in keys)
        p = E_soft[key]
        logL = math.log(p) if expected else math.log(1 - p)
        group_logL[g] += logL
        group_cnt[g] += 1
    total_logL = sum(GROUP_WEIGHTS[g] * (group_logL[g] / group_cnt[g]) for g in groups if group_cnt[g])
    log_likelihoods[scen] = total_logL

# posterior ∝ prior * exp(logL)
unnorm = {scen: priors[scen] * math.exp(logL) for scen, logL in log_likelihoods.items()}
total = sum(unnorm.values())
posteriors = {scen: v / total for scen, v in unnorm.items()}

print("=== ALGORITHM 2: BAYESIAN UPDATE ===")
print(f"{'Scenario':<32} {'Prior':>7} {'logL':>9} {'Posterior':>10}")
order = ["A_old_inflation", "B_ai_solution", "C_stagflation_loss", "D_deflation_bust"]
labels = {
    "A_old_inflation": "A 老剧本严格重演",
    "B_ai_solution": "B AI 化解滞胀",
    "C_stagflation_loss": "C 滞胀失控",
    "D_deflation_bust": "D 通缩型破裂",
}
for k in order:
    print(f"  {labels[k]:<30} {priors[k]*100:>6.1f}% {log_likelihoods[k]:>9.3f} {posteriors[k]*100:>9.1f}%")
print(f"\n  Δ vs prior: A {posteriors['A_old_inflation']-priors['A_old_inflation']:+.1%} | "
      f"B {posteriors['B_ai_solution']-priors['B_ai_solution']:+.1%} | "
      f"C {posteriors['C_stagflation_loss']-priors['C_stagflation_loss']:+.1%} | "
      f"D {posteriors['D_deflation_bust']-priors['D_deflation_bust']:+.1%}")

result = {
    "algorithm": "alg2_bayesian_update",
    "method": "shrinkage p_soft=0.075+0.85p; group-averaged logL (X1..X4 weights 0.30/0.25/0.25/0.20)",
    "priors": {k: round(v, 4) for k, v in priors.items()},
    "evidence_states": {k: round(v, 4) for k, v in E.items()},
    "evidence_softened": {k: round(v, 4) for k, v in E_soft.items()},
    "log_likelihoods": {k: round(v, 4) for k, v in log_likelihoods.items()},
    "posteriors": {k: round(v, 4) for k, v in posteriors.items()},
    "data": {"wti_now": wti_now, "ffr_now": ffr_now, "china_cpi_now": china_cpi_now},
}
with (OUT / "alg2_bayesian_update.json").open("w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print("\nSaved alg2_bayesian_update.json")