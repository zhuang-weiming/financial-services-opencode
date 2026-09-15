#!/usr/bin/env python3
"""BT-020 v2 — 修正重叠样本偏差: 加入"非重叠事件"选择 (forward 窗口不重叠).

问题: 深度回撤状态持续数百个交易日 → 朴素 episode ("连续日聚首日") 仍会产生大量
      伪独立事件 (同行业同一轮熊市被切成 10+ 个 episode, 如 801010 在 2001-2005)。
      而"全部事件日"口径 (n=6849) 严重重叠, 把 2005/2008/2014/2019 几个市场大底
      重复计数数千次 → 虚假的 +58% 中位。

修正: 非重叠选择 —— 事件按时间排序, 贪心选取, 与上一个已选事件间隔 >= min_gap
      交易日 (默认 120 = forward 窗口长度)。得到 forward 窗口互不重叠的独立事件。
      另做"市场级独立 episode": 同一日历事件窗内所有处于深回撤的行业取等权平均,
      每个独立事件窗只贡献 1 个观测。
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import load, build_features, HORIZONS, describe

BASE = Path(__file__).resolve().parent


def nonoverlap(df, dd_thr, dur_thr, min_gap=120):
    """按期非重叠贪心选择 (按 date 排序, 与上一选中日期间隔>=min_gap 交易日)."""
    ev = df[(df["dd"] <= dd_thr) & (df["dur"] >= dur_thr)].sort_values("date").copy()
    if ev.empty:
        return ev
    dates = ev["date"].values
    picked = []
    last = None
    for i, d in enumerate(dates):
        if last is None:
            picked.append(i)
            last = d
        else:
            # 交易日间隔用位置差近似: 用 numpy datetime 差换算
            if (d - last) / np.timedelta64(1, "D") >= int(min_gap * 1.45):
                picked.append(i)
                last = d
    return ev.iloc[picked].reset_index(drop=True)


def market_episodes(df, dd_thr, dur_thr, min_gap=120):
    """市场级独立事件: 每个独立事件窗内, 跨行业等权平均 forward 收益."""
    ev = df[(df["dd"] <= dd_thr) & (df["dur"] >= dur_thr)].sort_values("date")
    if ev.empty:
        return pd.DataFrame()
    dates = sorted(ev["date"].unique())
    picked = []
    last = None
    for d in dates:
        if last is None or (d - last) / np.timedelta64(1, "D") >= int(min_gap * 1.45):
            picked.append(pd.Timestamp(d))
            last = pd.Timestamp(d)
    rows = []
    for d in picked:
        sub = ev[ev["date"] == d]
        row = {"date": d, "n_industries": len(sub)}
        for h in HORIZONS:
            row[f"fwd{h}"] = float(sub[f"fwd{h}"].mean())
        row["dd_mean"] = float(sub["dd"].mean())
        m = sub["regime"].mode()
        row["regime"] = m.iloc[0] if len(m) else "range"
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    panel, csi = load()
    feat = build_features(panel, csi)
    # regime 需要 CSI300 252d 历史 → 2005-04 (CSI300 起点) 起 regime 才有定义
    feat = feat[feat["date"] >= pd.Timestamp("2005-04-08")].copy()
    panel = panel[panel.index >= pd.Timestamp("2005-04-08")]
    print("样本起点限制: 2005-04-08 (令 CSI300 regime 全样本有定义)")

    out = {}
    scenarios = [
        ("A_dd40_dur120", -0.40, 120),
        ("B_dd50_dur180", -0.50, 180),
        ("C_dd40_dur180", -0.40, 180),
    ]

    print("=" * 80)
    print("BT-020 v2 — 非重叠事件口径 (修正重叠样本偏差)")
    print("=" * 80)

    for name, dd_thr, dur_thr in scenarios:
        ev = nonoverlap(feat, dd_thr, dur_thr, 120)
        mk = market_episodes(feat, dd_thr, dur_thr, 120)
        out[name] = {
            "params": {"dd": dd_thr, "dur": dur_thr, "min_gap_days": 120},
            "nonoverlap_events": {
                "n": int(len(ev)),
                "all": {f"fwd{h}": describe(ev[f"fwd{h}"]) for h in HORIZONS},
                "by_regime": {reg: {f"fwd{h}": describe(ev.loc[ev["regime"] == reg, f"fwd{h}"])
                                    for h in HORIZONS} for reg in ["bull", "range", "bear"]},
            },
            "market_level_independent_episodes": {
                "n": int(len(mk)),
                "all": {f"fwd{h}": describe(mk[f"fwd{h}"]) for h in HORIZONS},
                "by_regime": {reg: {f"fwd{h}": describe(mk.loc[mk["regime"] == reg, f"fwd{h}"])
                                    for h in HORIZONS} for reg in ["bull", "range", "bear"]},
            },
        }
        print(f"\n[场景 {name}]  dd<={dd_thr:.0%}  dur>={dur_thr}d")
        print(f"  ── 非重叠个体事件 (n={len(ev)}) ──")
        for h in HORIZONS:
            s = out[name]["nonoverlap_events"]["all"][f"fwd{h}"]
            print(f"     fwd{h:>3}d: n={s['n']} mean={s['mean']:+.2f}% median={s['median']:+.2f}% "
                  f"win={s['win_rate']}% p25={s['p25']} p75={s['p75']}")
        print(f"  ── 市场级独立 episode (n={len(mk)}) ──")
        for h in HORIZONS:
            s = out[name]["market_level_independent_episodes"]["all"][f"fwd{h}"]
            print(f"     fwd{h:>3}d: n={s['n']} mean={s['mean']:+.2f}% median={s['median']:+.2f}% "
                  f"win={s['win_rate']}% p25={s['p25']} p75={s['p75']}")
        print("  ── 市场级 by regime (fwd120) ──")
        for reg in ["bull", "range", "bear"]:
            s = out[name]["market_level_independent_episodes"]["by_regime"][reg]["fwd120"]
            print(f"     [{reg}] {s}")
        if len(mk):
            mk.to_csv(BASE / f"market_episodes_{name}.csv", index=False)

    # 关键: 用户 563530 的形态 (回撤 ~46%, 持续 ~8 个月) 在历史中匹配到哪些事件
    print("\n" + "=" * 80)
    print("匹配 563530 形态的事件 (回撤 -40~-50% 区间, 持续 150-220 交易日, 首日)")
    ek = out["A_dd40_dur120"]
    evA = nonoverlap(feat, -0.40, 120, 120)
    near = evA[(evA["dd"] <= -0.38) & (evA["dd"] >= -0.52) & (evA["dur"] >= 150) & (evA["dur"] <= 230)]
    out["matched_563530_shape"] = {
        "n": int(len(near)),
        "fwd60": describe(near["fwd60"]), "fwd120": describe(near["fwd120"]),
    }
    print(f"  匹配事件 n={len(near)}")
    print(f"  fwd60 : {out['matched_563530_shape']['fwd60']}")
    print(f"  fwd120: {out['matched_563530_shape']['fwd120']}")
    for _, r in near.iterrows():
        f60 = "--" if pd.isna(r["fwd60"]) else f"{r['fwd60']*100:+.1f}%"
        f120 = "--" if pd.isna(r["fwd120"]) else f"{r['fwd120']*100:+.1f}%"
        print(f"    {str(r['date'].date())} {str(r['code'])[:12]:14s} dd={r['dd']*100:+.1f}% dur={int(r['dur']):3d} "
              f"{str(r['regime']):5s} fwd60={f60:>7s} fwd120={f120}")

    with open(BASE / "summary_v2.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print("\n[saved] summary_v2.json")


if __name__ == "__main__":
    main()
