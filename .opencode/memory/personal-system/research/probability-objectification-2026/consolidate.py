"""Probability-Objectification: Consolidated comparison of 3 algorithms.

Merges alg1/alg2/alg3 results + report original subjective probabilities,
computes the ensemble (equal-weight mean of the three objective methods),
and produces a final markdown table + JSON for the report update.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent

SCEN = ["A_old_inflation", "B_ai_solution", "C_stagflation_loss", "D_deflation_bust"]
LABELS = {
    "A_old_inflation": "A 老剧本严格重演 1966-82",
    "B_ai_solution": "B AI 化解滞胀 1995-99",
    "C_stagflation_loss": "C 滞胀失控 极端",
    "D_deflation_bust": "D 通缩型破裂 2000-02+2007-09",
}
SHORT = {"A_old_inflation": "A", "B_ai_solution": "B", "C_stagflation_loss": "C", "D_deflation_bust": "D"}


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text())


def main() -> None:
    r1 = load("alg1_signal_scoring.json")
    r2 = load("alg2_bayesian_update.json")
    r3 = load("alg3_historical_similarity.json")

    p1 = r1["probabilities"]
    p2 = r2["posteriors"]
    p3 = r3["scenario_probabilities"]
    original = {"A_old_inflation": 0.30, "B_ai_solution": 0.30, "C_stagflation_loss": 0.15, "D_deflation_bust": 0.25}

    # Ensemble: mean of the three objective methods
    ens = {s: (p1[s] + p2[s] + p3[s]) / 3.0 for s in SCEN}
    ens_total = sum(ens.values())
    ens = {s: v / ens_total for s, v in ens.items()}

    # Ensemble with original included (4-way, for reference if user wants)
    ens4 = {s: (original[s] + p1[s] + p2[s] + p3[s]) / 4.0 for s in SCEN}
    ens4_total = sum(ens4.values())
    ens4 = {s: v / ens4_total for s, v in ens4.items()}

    rows = []
    for s in SCEN:
        rows.append({
            "Scenario": SHORT[s],
            "Label": LABELS[s],
            "Original_主观": round(original[s] * 100, 1),
            "Alg1_信号计分": round(p1[s] * 100, 1),
            "Alg2_贝叶斯": round(p2[s] * 100, 1),
            "Alg3_历史相似": round(p3[s] * 100, 1),
            "Ensemble_3法均值": round(ens[s] * 100, 1),
            "Ensemble_含原判断": round(ens4[s] * 100, 1),
            "Δ_Ens3_vs_原": round((ens[s] - original[s]) * 100, 1),
        })
    df = pd.DataFrame(rows)
    print("=== CONSOLIDATED SCENARIO PROBABILITIES (%) ===")
    print(df.to_string(index=False))

    result = {
        "algorithm": "ensemble",
        "original": {SHORT[k]: round(v * 100, 1) for k, v in original.items()},
        "alg1_signal_scoring": {SHORT[k]: round(v * 100, 1) for k, v in p1.items()},
        "alg2_bayesian": {SHORT[k]: round(v * 100, 1) for k, v in p2.items()},
        "alg3_historical": {SHORT[k]: round(v * 100, 1) for k, v in p3.items()},
        "ensemble_3objective": {SHORT[k]: round(v * 100, 1) for k, v in ens.items()},
        "ensemble_4way_with_original": {SHORT[k]: round(v * 100, 1) for k, v in ens4.items()},
        "note": "Alg1=signal scoring; Alg2=Bayesian update w/ shrinkage+group weights; Alg3=historical similarity; Ensemble=mean of 3 objective methods",
    }
    with (OUT / "final_consolidated.json").open("w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Markdown table for report insertion
    md = []
    md.append("| 剧本 | 原主观概率 | Alg1 信号计分 | Alg2 贝叶斯 | Alg3 历史相似 | **三法均值** | Δ vs 原 |")
    md.append("|:-----|----------:|-----------:|----------:|-----------:|-----------:|-------:|")
    for _, r in df.iterrows():
        md.append(f"| {r['Scenario']} ({r['Label']}) | {r['Original_主观']:.1f}% | {r['Alg1_信号计分']:.1f}% | {r['Alg2_贝叶斯']:.1f}% | {r['Alg3_历史相似']:.1f}% | **{r['Ensemble_3法均值']:.1f}%** | {r['Δ_Ens3_vs_原']:+.1f}pp |")
    md_text = "\n".join(md)
    (OUT / "final_table.md").write_text(md_text)
    print("\n=== MARKDOWN TABLE ===")
    print(md_text)
    print("\nSaved final_consolidated.json + final_table.md")


if __name__ == "__main__":
    main()