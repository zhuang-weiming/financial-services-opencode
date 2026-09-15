#!/usr/bin/env python3
"""BT-020 补充 — 回撤深度分桶 (检验"跌得越多=未来越好"单调性) + episode 明细."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import load, build_features, HORIZONS

BASE = Path(__file__).resolve().parent
feat = None


def main():
    panel, csi = load()
    feat = build_features(panel, csi)

    print("=" * 78)
    print("补充 A: 回撤深度分桶 → forward 收益 (检验单调性: 跌得越多是否未来越好)")
    print("=" * 78)
    bins = [-1.01, -0.60, -0.40, -0.20, -0.0001, 1.01]
    labels = ["<-60%", "-60~-40%", "-40~-20%", "-20~0%", ">0% (新高)"]
    feat["dd_bucket"] = pd.cut(feat["dd"], bins=bins, labels=labels)
    out = {}
    for lab in labels:
        sub = feat[feat["dd_bucket"] == lab]
        row = {}
        for h in HORIZONS:
            x = sub[f"fwd{h}"].dropna()
            row[f"fwd{h}"] = {
                "n": int(len(x)),
                "mean": round(float(x.mean()) * 100, 2),
                "median": round(float(x.median()) * 100, 2),
                "win": round(float((x > 0).mean()) * 100, 1),
            }
        out[lab] = row
        print(f"  回撤 {lab:12s} n={row['fwd120']['n']:6d} | "
              f"fwd60 median={row['fwd60']['median']:+.2f}% | "
              f"fwd120 mean={row['fwd120']['mean']:+.2f}% median={row['fwd120']['median']:+.2f}% "
              f"win={row['fwd120']['win']}%")

    print("\n" + "=" * 78)
    print("补充 B: 回撤持续时间分桶 (控制回撤<=-40%)")
    print("=" * 78)
    deep = feat[feat["dd"] <= -0.40].copy()
    dur_bins = [120, 180, 250, 500, 10000]
    dur_labels = ["120-180d", "180-250d", "250-500d", ">500d"]
    deep["dur_bucket"] = pd.cut(deep["dur"], bins=dur_bins, labels=dur_labels)
    out2 = {}
    for lab in dur_labels:
        sub = deep[deep["dur_bucket"] == lab]
        x = sub["fwd120"].dropna()
        if len(x) == 0:
            continue
        out2[lab] = {"n": int(len(x)), "mean": round(float(x.mean()) * 100, 2),
                     "median": round(float(x.median()) * 100, 2),
                     "win": round(float((x > 0).mean()) * 100, 1)}
        print(f"  回撤持续 {lab:10s} 事件日 n={len(x):5d} fwd120 mean={out2[lab]['mean']:+.2f}% "
              f"median={out2[lab]['median']:+.2f}% win={out2[lab]['win']}%")

    print("\n" + "=" * 78)
    print("补充 C: 场景A (dd<=-40%,dur>=120d) 41 个 episode 明细 (含 regime)")
    print("=" * 78)
    ev = pd.read_csv(BASE / "events_dd40_dur120.csv")
    ev["date"] = pd.to_datetime(ev["date"])
    for _, r in ev.sort_values("date").iterrows():
        code = str(r["code"])[:12]
        f60 = "--" if pd.isna(r["fwd60"]) else f"{r['fwd60'] * 100:+.1f}%"
        f120 = "--" if pd.isna(r["fwd120"]) else f"{r['fwd120'] * 100:+.1f}%"
        print(f"  {str(r['date'].date())}  {code:14s} dd={r['dd'] * 100:6.1f}% dur={int(r['dur']):3d}  "
              f"{str(r['regime']):5s}  fwd60={f60:>7s}  fwd120={f120}")

    with open(BASE / "supplementary.json", "w") as f:
        json.dump({"dd_buckets": out, "dur_buckets": out2}, f, ensure_ascii=False, indent=2, default=str)
    print("\n[saved] supplementary.json")


if __name__ == "__main__":
    main()
