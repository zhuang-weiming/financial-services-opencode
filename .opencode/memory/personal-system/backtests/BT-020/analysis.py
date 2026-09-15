#!/usr/bin/env python3
"""BT-020 — "深度回撤 + 时间够长 → 未来 6 个月修复" 在 A 股板块指数层面的检验.

用户论证: "距离高点已下跌近 50%, 时间 9 个月 → 估值到位 → 未来 6 个月修复"
(即 BT-007 的 deep-recovery 模式从单股推广到 ETF/板块级)

方法:
  1. 宇宙 = 申万一级行业指数 31 个 (1999-12 → 现在, 官方价格指数)
  2. 事件定义 A (主): 自 252 交易日 (12m) 高点的回撤 <= -40% 且 回撤持续 >= 120 交易日 (6m)
     事件定义 B (稳健): 回撤 <= -50% 且 持续 >= 180 交易日 (9m, 贴近用户"9 个月")
  3. forward: 60d / 120d 收盘到收盘 (无 lookahead: t 时点仅用 t 及之前信息)
  4. 事件聚集: 连续事件日合并为 1 个 episode (取首日) —— 避免重叠样本膨胀 n
  5. regime 分层: 沪深300 滚动 252d 收益 <-15% 熊 / >+15% 牛 / 其余震荡
  6. LAW-002: 同时报 mean 与 median

局限 (诚实边界):
  - 行业指数为价格指数 (不含分红再投), 与 ETF 净值口径不完全一致
  - 申万一级行业 2021 版分类前推到 1999 年, 早期样本存在分类回填口径问题
  - 事件高度重叠 → 即使做 episode 聚类, 相邻 episode 仍非独立
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
HORIZONS = [20, 60, 120]
PRIMARY_DD = -0.40
PRIMARY_DUR = 120
STRICT_DD = -0.50
STRICT_DUR = 180


def load():
    panel = pd.read_csv(DATA / "sw_l1_close.csv", index_col=0, parse_dates=True).sort_index()
    csi = pd.read_csv(DATA / "csi300_close.csv", parse_dates=["date"]).set_index("date")["close"].sort_index()
    csi = csi[~csi.index.duplicated(keep="last")]
    return panel, csi


def days_since_rolling_max(s: pd.Series, win: int = 252) -> pd.Series:
    """每个时点距其 trailing win 窗口内最高点的交易日数 (0 = 今日即最高)."""
    vals = s.values
    n = len(vals)
    out = np.full(n, np.nan)
    for i in range(win - 1, n):
        w = vals[i - win + 1:i + 1]
        if np.all(np.isnan(w)):
            continue
        out[i] = (win - 1) - int(np.nanargmax(w))
    return pd.Series(out, index=s.index)


def build_features(panel, csi):
    """返回 long-form DataFrame: date, code, close, dd, dur, regime, fwd_*"""
    roll_max = panel.rolling(252, min_periods=252).max()
    dd = panel / roll_max - 1.0
    dur = panel.apply(lambda s: days_since_rolling_max(s, 252), axis=0)

    csi_ret252 = csi / csi.shift(252) - 1.0
    regime = pd.Series("range", index=csi.index)
    regime[csi_ret252 < -0.15] = "bear"
    regime[csi_ret252 > 0.15] = "bull"

    fwd = {}
    for h in HORIZONS:
        fwd[h] = panel.shift(-h) / panel - 1.0

    rows = []
    for code in panel.columns:
        d = pd.DataFrame({
            "close": panel[code],
            "dd": dd[code],
            "dur": dur[code],
        })
        d["regime"] = regime.reindex(d.index).ffill()
        for h in HORIZONS:
            d[f"fwd{h}"] = fwd[h][code]
        d["code"] = code
        d = d.dropna(subset=["dd", "dur"])
        rows.append(d.reset_index().rename(columns={"index": "date"}))
    return pd.concat(rows, ignore_index=True)


def episodes(d, dd_thr, dur_thr):
    """筛事件 + 连续事件日聚成 episode (取首日)."""
    ev = d[(d["dd"] <= dd_thr) & (d["dur"] >= dur_thr)].sort_values("date")
    if ev.empty:
        return ev
    new_ep = (ev["date"].diff().dt.days.fillna(999) > 7).astype(int)
    ev = ev.copy()
    ev["episode"] = new_ep.cumsum()
    return ev.groupby("episode").first().reset_index(drop=True)


def describe(x):
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return dict(n=0)
    return dict(
        n=int(len(x)), mean=round(float(x.mean()) * 100, 2),
        median=round(float(x.median()) * 100, 2),
        win_rate=round(float((x > 0).mean()) * 100, 1),
        p25=round(float(x.quantile(.25)) * 100, 2),
        p75=round(float(x.quantile(.75)) * 100, 2),
        min=round(float(x.min()) * 100, 1),
        max=round(float(x.max()) * 100, 1),
    )


def main():
    panel, csi = load()
    feat = build_features(panel, csi)

    out = {}
    print("=" * 78)
    print("BT-020 深度回撤→修复 事件研究 (申万一级行业指数 31)")
    print(f"面板: {panel.shape[1]} 行业 × {len(panel)} 日  ({panel.index[0].date()} → {panel.index[-1].date()})")
    print("=" * 78)

    # 无条件基线
    out["baseline_all_days"] = {f"fwd{h}": describe(feat[f"fwd{h}"]) for h in HORIZONS}
    print("\n[基线] 全样本无条件 forward 收益:")
    for h in HORIZONS:
        print(f"  fwd{h:>3}d: {out['baseline_all_days'][f'fwd{h}']}")

    scenarios = [
        ("A_dd40_dur120", PRIMARY_DD, PRIMARY_DUR),
        ("B_dd50_dur180", STRICT_DD, STRICT_DUR),
        ("C_dd40_dur180", -0.40, 180),
        ("D_dd50_dur120", -0.50, 120),
    ]
    for name, dd_thr, dur_thr in scenarios:
        ev = episodes(feat, dd_thr, dur_thr)
        out[name] = {
            "params": {"dd_thr": dd_thr, "dur_thr": dur_thr},
            "n_raw_event_days": int(((feat["dd"] <= dd_thr) & (feat["dur"] >= dur_thr)).sum()),
            "n_episodes": int(len(ev)),
            "span": [str(ev["date"].min().date()), str(ev["date"].max().date())] if len(ev) else None,
            "all": {f"fwd{h}": describe(ev[f"fwd{h}"]) for h in HORIZONS},
            "by_regime": {
                reg: {f"fwd{h}": describe(ev.loc[ev["regime"] == reg, f"fwd{h}"]) for h in HORIZONS}
                for reg in ["bull", "range", "bear"]
            },
        }
        print(f"\n[场景 {name}] dd<={dd_thr:.0%}, dur>={dur_thr}d  "
              f"| 原始事件日={out[name]['n_raw_event_days']} → 独立 episode={out[name]['n_episodes']}")
        if out[name]["span"]:
            print(f"  样本区间: {out[name]['span'][0]} → {out[name]['span'][1]}")
        for h in HORIZONS:
            s = out[name]["all"][f"fwd{h}"]
            print(f"  fwd{h:>3}d: n={s.get('n')}  mean={s.get('mean')}%  median={s.get('median')}%  "
                  f"win={s.get('win_rate')}%  p25={s.get('p25')}  p75={s.get('p75')}")
        for reg in ["bull", "range", "bear"]:
            s = out[name]["by_regime"][reg]["fwd120"]
            print(f"    [{reg}] fwd120: {s}")

    # 军工 (最贴近卫星主题) 单板块
    ty = feat[feat["code"].str.contains("国防军工")]
    ev_ty = episodes(ty, PRIMARY_DD, PRIMARY_DUR)
    out["defense_sector_only"] = {
        "n_episodes": int(len(ev_ty)),
        "all": {f"fwd{h}": describe(ev_ty[f"fwd{h}"]) for h in HORIZONS},
    }
    print(f"\n[国防军工单板块] dd<=-40% & dur>=120d: episodes={len(ev_ty)}")
    for h in HORIZONS:
        print(f"  fwd{h:>3}d: {out['defense_sector_only']['all'][f'fwd{h}']}")

    # 条件概率: 处于深度回撤的行业, 未来 120d 跑赢/跑输中位
    import json
    with open(BASE / "summary.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    # 事件明细 csv
    ev = episodes(feat, PRIMARY_DD, PRIMARY_DUR)
    ev.to_csv(BASE / "events_dd40_dur120.csv", index=False)
    print(f"\n[saved] summary.json / events_dd40_dur120.csv  (episodes={len(ev)})")


if __name__ == "__main__":
    main()
