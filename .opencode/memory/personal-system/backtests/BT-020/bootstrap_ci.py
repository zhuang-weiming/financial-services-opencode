#!/usr/bin/env python3
"""BT-020 补充 — 对关键口径做 bootstrap 95% CI (median), 量化小样本不确定性."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import load, build_features
from analysis_v2 import nonoverlap, market_episodes

BASE = Path(__file__).resolve().parent
rng = np.random.default_rng(42)


def boot_median(x, n=10000):
    x = np.asarray(pd.Series(x).dropna())
    if len(x) < 2:
        return None
    meds = [np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)]
    return {
        "n": int(len(x)),
        "median": round(float(np.median(x)) * 100, 2),
        "ci95_lo": round(float(np.percentile(meds, 2.5)) * 100, 2),
        "ci95_hi": round(float(np.percentile(meds, 97.5)) * 100, 2),
        "p_median_gt0": round(float(np.mean(np.array(meds) > 0)), 3),
    }


def main():
    panel, csi = load()
    feat = build_features(panel, csi)
    feat = feat[feat["date"] >= pd.Timestamp("2005-04-08")].copy()

    out = {"sample_start": "2005-04-08", "n_bootstrap": 10000, "seed": 42}
    cases = {}

    for name, dd, dur in [("A_dd40_dur120", -0.40, 120), ("C_dd40_dur180", -0.40, 180)]:
        mk = market_episodes(feat, dd, dur, 120)
        cases[f"{name}_market"] = {
            "fwd60": boot_median(mk["fwd60"]), "fwd120": boot_median(mk["fwd120"])}

    evA = nonoverlap(feat, -0.40, 120, 120)
    near = evA[(evA["dd"] <= -0.38) & (evA["dd"] >= -0.52) & (evA["dur"] >= 150) & (evA["dur"] <= 230)]
    cases["matched_563530_shape"] = {
        "desc": "dd -38~-52%, dur 150-230d",
        "fwd60": boot_median(near["fwd60"]), "fwd120": boot_median(near["fwd120"]),
    }

    out["cases"] = cases
    print("=" * 74)
    print("BT-020 bootstrap 95% CI (median forward return, 2005-04+)")
    print("=" * 74)
    for k, v in cases.items():
        print(f"\n{k}:")
        for h in ["fwd60", "fwd120"]:
            s = v[h]
            if s:
                print(f"  {h}: n={s['n']} median={s['median']:+.2f}%  "
                      f"95%CI=[{s['ci95_lo']:+.2f}%, {s['ci95_hi']:+.2f}%]  P(median>0)={s['p_median_gt0']}")

    with open(BASE / "bootstrap_ci.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print("\n[saved] bootstrap_ci.json")


if __name__ == "__main__":
    main()
