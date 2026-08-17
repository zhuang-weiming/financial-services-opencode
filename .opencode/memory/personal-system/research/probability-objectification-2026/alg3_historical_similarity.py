"""Probability-Objectification Algorithm 3: Historical Similarity Matching.

Goal: use the report's own historical analogues (1971.8 / 2000.3 / 2007.10 /
2021-23) as reference states, and compute how similar the CURRENT macro state
is to each, then translate similarity into scenario probabilities.

Method:
  1. Load anchor feature table (prepared from LOCAL REAL data: FRED + WIF CSVs).
  2. Load current snapshot (report §5.1 real values).
  3. For each anchor, compute a normalized distance across the available
     overlapping features (z-score each feature across anchors+current, then
     Euclidean distance). Fewer missing features -> more reliable.
  4. Convert distance to similarity = 1/(1+d) (bounded [0,1]).
  5. Map each anchor to its report scenario:
       1971.8  -> A 老剧本 (stagflation, current position stage-2)
       2000.3  -> D 通缩型破裂 (dot-com bust)
       2007.10 -> D 通缩型破裂 (GFC, secondary similarity)
       2021-23 -> C 滞胀失控 (mini-stagflation, tight Fed)
     and 1971.8 also informs B partially (report §4: current is a hybrid of
     '2021-23 mini + 1966-82 real-asset').
  6. Anchor similarity -> scenario probability via a mapping matrix with
     explicit weights (documented, adjustable).

Data source audit:
  - FRED local bulk: CPIAUCSL/DGS10/FEDFUNDS/DCOILWTICO/REAINTRATREARAT10Y (1947-2015)
  - WIF DGS10_2007_2026 (fills 10Y gap)
  - Current snapshot from report §5.1 (2026-08-16)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import numpy as np

OUT = Path(__file__).resolve().parent

FEATURES = ["cpi_yoy_pct", "gs10_pct", "ffr_pct", "real10_pct", "wti_usd", "credit_bp", "gold_usd"]

# anchor -> report scenario mapping (report §5.3 scenario labels)
# 1971.8 is the report's own primary analogue for A; but §4 says current is a
# HYBRID: 1966-82 real-asset strength (A) + 2021-23 Fed-active (C).
ANCHOR_SCENARIO = {
    "1971.8_nixon": {"A_old_inflation": 0.55, "C_stagflation_loss": 0.35, "B_ai_solution": 0.10},
    "2000.3_dotcom": {"D_deflation_bust": 0.90, "B_ai_solution": 0.10},
    "2007.10_gfc": {"D_deflation_bust": 0.90, "B_ai_solution": 0.10},
    "2021-23_mini": {"C_stagflation_loss": 0.60, "B_ai_solution": 0.40},
}

SCENARIOS = ["A_old_inflation", "B_ai_solution", "C_stagflation_loss", "D_deflation_bust"]


def main() -> None:
    anchors = pd.read_csv(OUT / "anchor_features.csv", index_col=0)
    current = pd.read_csv(OUT / "current_snapshot.csv", index_col=0)

    # Combine anchors + current into one feature frame
    comb = pd.concat([anchors, current])
    # z-score across all rows (per feature); this standardizes scale differences
    comb_z = (comb - comb.mean()) / comb.std()

    print("=== Z-SCORED FEATURE TABLE ===")
    print(comb_z.round(2).to_string())

    cur_key = "2026_current"
    distances = {}
    overlap = {}
    for anchor in anchors.index:
        mask = comb_z.loc[[anchor, cur_key]].dropna(axis=1)
        n_feat = mask.shape[1]
        d = float(np.linalg.norm(mask.loc[anchor] - mask.loc[cur_key]))
        distances[anchor] = d
        overlap[anchor] = n_feat
        print(f"\n  {anchor}: distance={d:.3f} (overlap features={n_feat})")

    # similarity = 1/(1+d)
    sim = {a: 1.0 / (1.0 + d) for a, d in distances.items()}
    print("\n=== SIMILARITY (1/(1+d)) ===")
    for a, s in sim.items():
        print(f"  {a:15s}: similarity={s:.3f}  (features used={overlap[a]})")

    # Weight similarity by feature overlap (more features = more reliable)
    max_feat = max(overlap.values())
    reliability = {a: overlap[a] / max_feat for a in anchors.index}
    sim_w = {a: sim[a] * reliability[a] for a in anchors.index}
    total_w = sum(sim_w.values())
    sim_norm = {a: v / total_w for a, v in sim_w.items()}

    print("\n=== OVERLAP-RELIABILITY WEIGHTED SIMILARITY (normalized) ===")
    for a, v in sim_norm.items():
        print(f"  {a:15s}: weight={v:.3f}")

    # Map anchor weights -> scenario probabilities
    scen_score = {s: 0.0 for s in SCENARIOS}
    for a, w in sim_norm.items():
        for s, contrib in ANCHOR_SCENARIO[a].items():
            scen_score[s] += w * contrib

    total = sum(scen_score.values())
    probs = {s: v / total for s, v in scen_score.items()}

    print("\n=== ALGORITHM 3: HISTORICAL SIMILARITY SCENARIO PROBABILITIES ===")
    labels = {
        "A_old_inflation": "A 老剧本严格重演 (1966-82)",
        "B_ai_solution": "B AI 化解滞胀 (1995-99)",
        "C_stagflation_loss": "C 滞胀失控 (极端)",
        "D_deflation_bust": "D 通缩型破裂 (2000-02+2007-09)",
    }
    for s in SCENARIOS:
        print(f"  {labels[s]:<36} {probs[s]*100:.1f}%")
    print("  (report original: A 30% / B 30% / C 15% / D 25%)")

    result = {
        "algorithm": "alg3_historical_similarity",
        "method": "z-score features across anchors+current; Euclidean distance; sim=1/(1+d); overlap-reliability weighting; anchor->scenario mapping matrix",
        "zscored": comb_z.round(4).to_dict(orient="index"),
        "distances": {k: round(v, 4) for k, v in distances.items()},
        "overlap_features": overlap,
        "similarity_raw": {k: round(v, 4) for k, v in sim.items()},
        "similarity_weighted_norm": {k: round(v, 4) for k, v in sim_norm.items()},
        "anchor_scenario_matrix": ANCHOR_SCENARIO,
        "scenario_probabilities": {k: round(v, 4) for k, v in probs.items()},
        "original": {"A": 0.30, "B": 0.30, "C": 0.15, "D": 0.25},
    }
    with (OUT / "alg3_historical_similarity.json").open("w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved alg3_historical_similarity.json")


if __name__ == "__main__":
    main()