#!/usr/bin/env python3
"""BT-021 补充 — IPO 活动 vs 板块 forward 收益: 显著性 + 子期稳健性 + 军工专题."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent


def r_ttest(x, y):
    d = pd.concat([x, y], axis=1).dropna()
    if len(d) < 5:
        return None
    r = d.iloc[:, 0].corr(d.iloc[:, 1])
    n = len(d)
    t = r * np.sqrt(n - 2) / np.sqrt(1 - r ** 2) if abs(r) < 1 else np.nan
    return dict(r=round(float(r), 3), n=int(n), t=round(float(t), 2))


def main():
    ipo = pd.read_csv(BASE / "ipo_monthly_enriched.csv", parse_dates=["date"]).set_index("date")
    bt006 = BASE.parent / "BT-006" / "data"
    secs = {"券商_非银金融": "801790", "电子": "801080", "计算机": "801750",
            "通信": "801770", "国防军工": "801740"}
    px = {}
    for nm, code in secs.items():
        d = pd.read_csv(bt006 / f"sw_l1_{code}.csv")
        d["date"] = pd.to_datetime(d["date"])
        px[nm] = d.set_index("date")["close"]
    csi = pd.read_csv(bt006 / "csi300_daily.csv")
    csi["date"] = pd.to_datetime(csi["date"])
    px["沪深300"] = csi.set_index("date")["close"]
    px = pd.DataFrame(px).resample("ME").last()

    ipo = ipo.reindex(px.index)

    out = {}
    print("=" * 78)
    print("BT-021 补充: IPO 月度家数 vs 板块 fwd6m 收益 — 相关性 + t 检验")
    print("=" * 78)
    for nm in px.columns:
        f6 = px[nm].shift(-6) / px[nm] - 1
        res = r_ttest(ipo["ipo_count"], f6)
        out[nm] = {"full": res}
        print(f"  {nm:12s} r={res['r']:+.3f}  n={res['n']}  t={res['t']:+.2f}  "
              f"→ {'显著负' if res['t'] < -1.96 else ('显著正' if res['t'] > 1.96 else '不显著')}")

    print("\n" + "=" * 78)
    print("子期稳健性 (IPO 家数 vs fwd6m):")
    print("=" * 78)
    subs = {"2010-2015": ("2010-01", "2015-12"), "2016-2020": ("2016-01", "2020-12"),
            "2021-2026": ("2021-01", "2026-07")}
    for nm in px.columns:
        line = [f"  {nm:12s}"]
        f6 = px[nm].shift(-6) / px[nm] - 1
        for lbl, (a, b) in subs.items():
            sub = ipo.loc[a:b]
            res = r_ttest(sub["ipo_count"], f6.reindex(sub.index))
            out[nm][lbl] = res
            line.append(f"{lbl}: r={res['r']:+.2f}(t={res['t']:+.1f},n={res['n']})" if res else f"{lbl}: n/a")
        print("  ".join(line))

    print("\n" + "=" * 78)
    print("国防军工 (最贴近卫星主题) 专题:")
    print("=" * 78)
    ty = px["国防军工"]
    f6 = ty.shift(-6) / ty - 1
    f3 = ty.shift(-3) / ty - 1
    q = ipo["ipo_count"].quantile([1/3, 2/3])
    for lbl, mask in [("高IPO月(top1/3)", ipo["ipo_count"] >= q.iloc[1]),
                      ("低IPO月(bot1/3)", ipo["ipo_count"] <= q.iloc[0])]:
        m = mask.reindex(f6.index).fillna(False)
        x6 = f6[m].dropna(); x3 = f3[m].dropna()
        print(f"  {lbl}: n={len(x6)} fwd3 median={x3.median()*100:+.2f}% "
              f"fwd6 mean={x6.mean()*100:+.2f}% median={x6.median()*100:+.2f}% win={ (x6>0).mean()*100:.0f}%")
    out["defense_high_ipo"] = {
        "fwd3_median": round(float(f3[ipo["ipo_count"] >= q.iloc[1]].dropna().median()) * 100, 2),
        "fwd6_median": round(float(f6[ipo["ipo_count"] >= q.iloc[1]].dropna().median()) * 100, 2),
    }
    out["defense_low_ipo"] = {
        "fwd3_median": round(float(f3[ipo["ipo_count"] <= q.iloc[0]].dropna().median()) * 100, 2),
        "fwd6_median": round(float(f6[ipo["ipo_count"] <= q.iloc[0]].dropna().median()) * 100, 2),
    }

    # 6 个板块符号一致性
    signs = [1 if out[nm]["full"]["r"] < 0 else -1 for nm in secs]
    out["sign_consistency"] = {"negative_count": int(sum(1 for s in signs if s == 1)), "total": len(signs)}
    print(f"\n符号一致性: {sum(1 for s in signs if s==1)}/{len(signs)} 板块为负相关")

    with open(BASE / "supplementary.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print("[saved] supplementary.json")


if __name__ == "__main__":
    main()
