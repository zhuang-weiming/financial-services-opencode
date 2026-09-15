#!/usr/bin/env python3
"""BT-021 — "IPO 热度 → 相关板块二级市场上涨" 机制检验.

用户论证 (卫星主题): "卫星/火箭领域 IPO 如火如荼 → 需要这个领域有高人气和热度,
否则 IPO 必然失败 → 卫星需要资金 → 股票需要大涨 → IPO 需要炒高"

BT-006 已对**完全同构的券商论证**做过检验并否定 (个股层面: 中银投行毛利率 -19.3%)。
本回测检验**市场层面**的机制: A 股历史上 IPO 密集期 / 科技 IPO 潮 与
(a) 券商板块 (承销受益方) (b) 科技板块 (发行主体) (c) 沪深300 的
**未来** 1m/3m/6m 收益 的关系 —— 是正相关 (情绪外溢/炒热) 还是负相关 (抽血/供给稀释)?

数据源: akshare stock_xgsglb_em (新股申购, 2010-2026) + index_hist_sw (申万行业) + 沪深300
注意: 本回测仅为研究工具, 不构成未来收益预测 (backtest-discipline 规则 1)。
"""
import json
import time
from pathlib import Path

import akshare as ak
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

SECTOR_MAP = {
    "券商_非银金融": "801790",
    "电子": "801080",
    "计算机": "801750",
    "通信": "801770",
    "国防军工": "801740",
    "沪深300": "000300",
}


def fetch_ipo():
    fp = DATA / "ipo_monthly.csv"
    if fp.exists():
        return pd.read_csv(fp, parse_dates=["month"])
    df = ak.stock_xgsglb_em()
    df["申购日期"] = pd.to_datetime(df["申购日期"], errors="coerce")
    df = df.dropna(subset=["申购日期"])
    df["发行价格"] = pd.to_numeric(df["发行价格"], errors="coerce")
    df["发行总数"] = pd.to_numeric(df["发行总数"], errors="coerce")
    # 发行总数单位=万股, 发行价格=元 → 募资额(万元)
    df["proceeds_wan"] = df["发行总数"] * df["发行价格"]
    df["month"] = pd.to_datetime(df["申购日期"]).dt.to_period("M").dt.to_timestamp("M")
    g = df.groupby("month").agg(
        ipo_count=("股票代码", "count"),
        ipo_proceeds_wan=("proceeds_wan", "sum"),
    ).reset_index()
    g.to_csv(fp, index=False)
    return g


def fetch_sectors():
    """优先复用 BT-006 本地缓存 (申万一级 + CSI300), 避免 akshare 申万接口限速."""
    bt006 = BASE.parent / "BT-006" / "data"
    frames = {}
    for name, code in SECTOR_MAP.items():
        if code == "000300":
            fp = bt006 / "csi300_daily.csv"
        else:
            fp = bt006 / f"sw_l1_{code}.csv"
        if fp.exists():
            d = pd.read_csv(fp)
            d["date"] = pd.to_datetime(d["date"])
            s = d[["date", "close"]].dropna().sort_values("date").set_index("date")["close"]
            s = s[~s.index.duplicated(keep="last")]
            frames[name] = s
            print(f"  {name} ({code}) [local cache]: {len(s)} bars ({s.index[0].date()} → {s.index[-1].date()})")
            continue
        # fallback: network
        if code == "000300":
            d = ak.index_zh_a_hist(symbol="000300", period="daily",
                                   start_date="20050101", end_date="20260930")
            d = d.rename(columns={"日期": "date", "收盘": "close"})
        else:
            d = ak.index_hist_sw(symbol=code, period="day")
            d = d.rename(columns={"日期": "date", "收盘": "close"})
        d["date"] = pd.to_datetime(d["date"])
        s = d[["date", "close"]].dropna().sort_values("date").set_index("date")["close"]
        frames[name] = s
        print(f"  {name} {code} [network]: {len(s)} bars")
        time.sleep(0.3)
    return pd.DataFrame(frames)


def forward_returns(px, months=1):
    """月度收盘的 forward N 月收益 (无 lookahead)."""
    m = px.resample("ME").last()
    return m.shift(-months) / m - 1.0


def main():
    print("[1] IPO 月度数据...")
    ipo = fetch_ipo()
    print(f"  {len(ipo)} 月 ({ipo['month'].min().date()} → {ipo['month'].max().date()})")
    print("[2] 板块指数...")
    px = fetch_sectors()

    m_close = px.resample("ME").last()
    ipo = ipo.set_index("month").reindex(m_close.index)
    ipo["ipo_count_3m"] = ipo["ipo_count"].rolling(3).sum()
    ipo["ipo_count_12m"] = ipo["ipo_count"].rolling(12).sum()

    out = {"meta": {
        "ipo_span": [str(ipo.index.min().date()), str(ipo.index.max().date())],
        "n_months": int(len(ipo)),
        "data_source": "akshare stock_xgsglb_em / index_hist_sw / index_zh_a_hist(000300)",
        "unit_note": "发行总数=万股 × 发行价格=元 → 募资额=万元",
    }}

    # --- A. 同期相关 & 领先相关 ---
    print("\n[A] IPO 活动 (月度家数) vs 板块收益 相关:")
    corr = {}
    for name in px.columns:
        f1 = forward_returns(px[name], 1)
        f3 = forward_returns(px[name], 3)
        f6 = forward_returns(px[name], 6)
        row = {
            "concurrent": round(float(ipo["ipo_count"].corr(m_close[name].pct_change())), 3),
            "fwd1m": round(float(ipo["ipo_count"].corr(f1)), 3),
            "fwd3m": round(float(ipo["ipo_count"].corr(f3)), 3),
            "fwd6m": round(float(ipo["ipo_count"].corr(f6)), 3),
            "fwd3m_lag3m_ipo": round(float(ipo["ipo_count_3m"].shift(3).corr(f3)), 3),
        }
        corr[name] = row
        print(f"  {name:12s} 同期={row['concurrent']:+.3f}  fwd1m={row['fwd1m']:+.3f}  "
              f"fwd3m={row['fwd3m']:+.3f}  fwd6m={row['fwd6m']:+.3f}")
    out["correlation"] = corr

    # --- B. 高/低 IPO 组的事件研究 ---
    print("\n[B] 按 IPO 活动分位的 forward 收益 (高=top tercile, 低=bottom tercile):")
    event = {}
    q = ipo["ipo_count"].quantile([1/3, 2/3])
    hi = ipo["ipo_count"] >= q.iloc[1]
    lo = ipo["ipo_count"] <= q.iloc[0]
    for name in px.columns:
        f6 = forward_returns(px[name], 6)
        f3 = forward_returns(px[name], 3)
        r = {
            "hi_n": int(hi.sum()), "lo_n": int(lo.sum()),
            "hi_fwd6_mean": round(float(f6[hi.reindex(f6.index)].dropna().mean()) * 100, 2),
            "hi_fwd6_median": round(float(f6[hi.reindex(f6.index)].dropna().median()) * 100, 2),
            "lo_fwd6_mean": round(float(f6[lo.reindex(f6.index)].dropna().mean()) * 100, 2),
            "lo_fwd6_median": round(float(f6[lo.reindex(f6.index)].dropna().median()) * 100, 2),
            "hi_fwd6_win": round(float((f6[hi.reindex(f6.index)].dropna() > 0).mean()) * 100, 1),
            "hi_fwd3_median": round(float(f3[hi.reindex(f3.index)].dropna().median()) * 100, 2),
        }
        event[name] = r
        print(f"  {name:12s} 高IPO组 fwd6 中位={r['hi_fwd6_median']:+.2f}% (均值{r['hi_fwd6_mean']:+.2f}%, 胜率{r['hi_fwd6_win']}%) "
              f"| 低IPO组 fwd6 中位={r['lo_fwd6_median']:+.2f}%")
    out["tercile_event"] = event

    # --- C. 2013 IPO 暂停自然实验 ---
    print("\n[C] 2013 IPO 暂停 (2012-11 → 2014-01) 自然实验:")
    segs = {"pre_2011": ("2011-01", "2012-10"), "freeze_2013": ("2012-11", "2013-12"),
            "reopen_2014": ("2014-01", "2014-12"), "post_2015": ("2015-01", "2015-12")}
    nat = {}
    for label, (a, b) in segs.items():
        m = m_close.loc[a:b]
        ret = (m.iloc[-1] / m.iloc[0] - 1) * 100 if len(m) > 1 else np.nan
        n_ipo = int(ipo.loc[a:b, "ipo_count"].sum())
        nat[label] = {"months": len(m), "ipo_count": n_ipo,
                      "ret_pct": {k: (round(float(v), 1) if pd.notna(v) else None) for k, v in ret.items()}}
        print(f"  {label:12s}: IPO家数={n_ipo:4d}  " +
              " ".join(f"{k}={'--' if v is None else f'{v:+.1f}%'}" for k, v in nat[label]["ret_pct"].items()))
    out["natural_experiment_2013"] = nat

    with open(BASE / "summary.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    ipo.to_csv(BASE / "ipo_monthly_enriched.csv")
    print("\n[saved] summary.json / ipo_monthly_enriched.csv")


if __name__ == "__main__":
    main()
