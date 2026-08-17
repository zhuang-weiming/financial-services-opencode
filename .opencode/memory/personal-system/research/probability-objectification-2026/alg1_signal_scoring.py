"""Probability-Objectification Algorithm 1: Signal Scoring.

Goal: replace the report's subjective scenario probabilities (30/30/15/25%)
with a data-driven signal score.

Method (transparent, auditable):
  Each of the 4 report variables X1-X4 is mapped to a *state probability*
  derived from real market data:
    X1 (AI Capex->productivity)  <- 4.2 AI bubble tracking 5-signal probabilities
                                     (Capex/Rev 85%, Leverage 70%, Focus shift 50%)
    X2 (Middle-East conflict)    <- WTI level vs report's scenario thresholds
                                     (D:<60 / B:75-95 / A:>100 / C:>150)
    X3 (Fed reaction)            <- FFR level vs report's scenario thresholds
                                     (D:<2.5 / B:3.5-4.5 / A:>=6 / C:failed-hawk)
    X4 (China/global demand)     <- China CPI vs report's thresholds
                                     (D:<0.5 crisis / soft 1-2 / B recovery)

  Each scenario A/B/C/D requires a specific combination of variable states
  (report §5.3). We score:
      scenario_score(S) = sum over required states of (state_prob * weight)
  then normalize to probabilities.

Data used:
  - 4.2 five-signal table (12-month trigger probabilities, 2026-08-04)
  - report §5.1 snapshot (FFR 3.63%, WTI 82.55, China CPI 0.5%)
  - report §5.3 scenario trigger thresholds
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

# ---- Input data (real, from 4.2 + report §5.1) ----
signal_probabilities = {
    "capex_rev": 0.85,      # 4.2 §2.6, triggered (GOOGL 37.5%, META 49.5%)
    "leverage": 0.70,       # 4.2 §2.6, triggered (ORCL 3.63, CRWV 8.94)
    "focus_shift": 0.50,    # 4.2 §2.6, in progress
    "rate_credit": 0.60,    # 4.2 §2.6, tightening (30Y 99.7%, Core PCE 100%)
    "gov_response": 0.30,   # 4.2 §2.6, zero policy response yet
}
wti_now = 82.55        # report §5.1, OilPrice.com 2026-08-16
ffr_now = 3.63         # report §5.1, FOMC midpoint 2026-07-29
china_cpi_now = 0.5    # report §5.1, China NBS 2026-07


# ---- Variable state probability functions (monotone / fuzzy thresholds) ----

def x1_ai_capex_states() -> dict:
    """X1: AI Capex->productivity. 'bust' probability = composite of bubble signals.
    'productivity' = complement, partially discounted by focus shift (mixed evidence)."""
    bust = 0.60 * signal_probabilities["capex_rev"] + 0.25 * signal_probabilities["leverage"] + 0.15 * signal_probabilities["focus_shift"]
    bust = min(0.95, bust)
    productivity = 1 - bust
    # 'partial' = the ambiguous middle (focus shift debate ongoing)
    partial = signal_probabilities["focus_shift"] * (1 - signal_probabilities["capex_rev"])
    return {"bust": bust, "productivity": productivity, "partial": partial}


def x2_conflict_states() -> dict:
    """X2: Middle-East conflict -> WTI threshold mapping (report §5.3).
    Fuzzy membership around the report's anchor levels."""
    s = {}
    s["de-escalation"] = _trap_rev(wti_now, 55, 70)              # D requires <60 -> inverse ramp
    s["flat_75_95"] = _trap_band(wti_now, 70, 75, 95, 100)       # B requires 75-95
    s["escalation_100"] = _ramp(wti_now, 95, 110)                # A requires >100
    s["extreme_150"] = _ramp(wti_now, 135, 165)                  # C requires >150 (Hormuz)
    return s


def x3_fed_states() -> dict:
    """X3: Fed reaction. FFR midpoint mapping.
    D requires surrender <2.5; B requires slow 3.5-4.5; A requires violent >=6;
    C requires credibility loss (below what stagflation would demand)."""
    s = {}
    s["surrender"] = _trap_rev(ffr_now, 2.0, 2.8)
    s["slow"] = _trap_band(ffr_now, 3.4, 3.5, 4.5, 4.6)
    s["violent"] = _ramp(ffr_now, 5.5, 6.0)
    s["lost_credibility"] = 0.5 * (1 - s["violent"]) + 0.35 * signal_probabilities["gov_response"]  # dovish pressure while CPI elevated
    return s


def x4_china_states() -> dict:
    """X4: China/global demand via China CPI.
    D crisis requires CPI<0.5 (& EM debt crisis); A/B soft = 1-2%; B recovery 1-2%+."""
    s = {}
    s["crisis"] = _trap(china_cpi_now, 0.2, 0.5) * 0.8 + 0.2 * signal_probabilities["rate_credit"]  # global fragility component
    s["soft_1_2"] = _trap_band(china_cpi_now, 0.7, 1.0, 2.0, 2.3)
    return s


def _trap(x: float, lo: float, hi: float) -> float:
    """Fuzzy membership: 0 below lo, 1 at/above hi, linear ramp."""
    if x <= lo:
        return 0.0
    if x >= hi:
        return 1.0
    return (x - lo) / (hi - lo)


def _trap_rev(x: float, lo: float, hi: float) -> float:
    """Inverse fuzzy membership: 1 below lo, 0 at/above hi (monotone decreasing)."""
    return 1.0 - _trap(x, lo, hi)


def _trap_band(x: float, lo_a: float, lo_b: float, hi_b: float, hi_a: float) -> float:
    """Band membership: rises to 1 between lo_a->lo_b, falls from hi_b->hi_a."""
    rise = _trap(x, lo_a, lo_b)
    fall = 1 - _trap(x, hi_b, hi_a)
    return max(0.0, min(rise, fall))


def _ramp(x: float, lo: float, hi: float) -> float:
    return _trap(x, lo, hi)


# ---- Scenario scoring ----
# Each scenario requires the states defined in report §5.3.
scenario_requirements = {
    # A: 老剧本  — X1 bust, X2 escalation>100, X3 violent>=6, X4 soft
    "A_old_inflation": {
        "states": ["x1_bust", "x2_escalation_100", "x3_violent", "x4_soft_1_2"],
        "weights": [0.35, 0.25, 0.25, 0.15],
        "label": "A 老剧本严格重演 (1966-82)",
    },
    # B: AI 化解 — X1 productivity, X2 flat 75-95, X3 slow, X4 soft/recovery
    "B_ai_solution": {
        "states": ["x1_productivity", "x2_flat_75_95", "x3_slow", "x4_soft_1_2"],
        "weights": [0.40, 0.20, 0.20, 0.20],
        "label": "B AI 化解滞胀 (1995-99)",
    },
    # C: 滞胀失控 — X2 extreme>150, X3 lost credibility, X1 partial, X4 stable
    "C_stagflation_loss": {
        "states": ["x2_extreme_150", "x3_lost_credibility", "x1_partial", "x4_soft_1_2"],
        "weights": [0.35, 0.30, 0.20, 0.15],
        "label": "C 滞胀失控 (极端)",
    },
    # D: 通缩型破裂 — X1 bust, X2 de-escalation<60, X3 surrender<2.5, X4 crisis
    "D_deflation_bust": {
        "states": ["x1_bust", "x2_de-escalation", "x3_surrender", "x4_crisis"],
        "weights": [0.35, 0.20, 0.20, 0.25],
        "label": "D 通缩型破裂 (2000-02+2007-09)",
    },
}

X1 = x1_ai_capex_states()
X2 = x2_conflict_states()
X3 = x3_fed_states()
X4 = x4_china_states()

state_values = {
    "x1_bust": X1["bust"],
    "x1_productivity": X1["productivity"],
    "x1_partial": X1["partial"],
    "x2_escalation_100": X2["escalation_100"],
    "x2_extreme_150": X2["extreme_150"],
    "x2_flat_75_95": X2["flat_75_95"],
    "x2_de-escalation": X2["de-escalation"],
    "x3_violent": X3["violent"],
    "x3_slow": X3["slow"],
    "x3_surrender": X3["surrender"],
    "x3_lost_credibility": X3["lost_credibility"],
    "x4_soft_1_2": X4["soft_1_2"],
    "x4_crisis": X4["crisis"],
}

scores = {}
for key, spec in scenario_requirements.items():
    sc = sum(w * state_values[s] for s, w in zip(spec["states"], spec["weights"]))
    scores[key] = sc

total = sum(scores.values())
probs = {k: v / total for k, v in scores.items()}

# ---- Output ----
print("=== VARIABLE STATE PROBABILITIES (from real data) ===")
print(f"X1 AI:  bust={state_values['x1_bust']:.2f}  productivity={state_values['x1_productivity']:.2f}  partial={state_values['x1_partial']:.2f}")
print(f"X2 WTI: de-escalation={state_values['x2_de-escalation']:.2f}  flat75-95={state_values['x2_flat_75_95']:.2f}  escal>100={state_values['x2_escalation_100']:.2f}  extreme>150={state_values['x2_extreme_150']:.2f}")
print(f"X3 FFR: surrender={state_values['x3_surrender']:.2f}  slow={state_values['x3_slow']:.2f}  violent={state_values['x3_violent']:.2f}  lost_cred={state_values['x3_lost_credibility']:.2f}")
print(f"X4 ChinaCPI: soft1-2={state_values['x4_soft_1_2']:.2f}  crisis={state_values['x4_crisis']:.2f}")
print("\n=== RAW SCORES ===")
for k, v in scores.items():
    print(f"  {scenario_requirements[k]['label']}: score={v:.3f}")
print("\n=== NORMALIZED PROBABILITIES (Algorithm 1) ===")
order = ["A_old_inflation", "B_ai_solution", "C_stagflation_loss", "D_deflation_bust"]
for k in order:
    print(f"  {scenario_requirements[k]['label']}: {probs[k]*100:.1f}%")
print(f"\n(report original: A 30% / B 30% / C 15% / D 25%)")

result = {
    "algorithm": "alg1_signal_scoring",
    "input_data": {
        "signal_probabilities": signal_probabilities,
        "wti_now": wti_now,
        "ffr_now": ffr_now,
        "china_cpi_now": china_cpi_now,
    },
    "state_values": {k: round(v, 4) for k, v in state_values.items()},
    "raw_scores": {k: round(v, 4) for k, v in scores.items()},
    "probabilities": {k: round(v, 4) for k, v in probs.items()},
    "original": {"A": 0.30, "B": 0.30, "C": 0.15, "D": 0.25},
}
with (OUT / "alg1_signal_scoring.json").open("w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\nSaved alg1_signal_scoring.json")