#!/usr/bin/env python3
"""BT-020 数据装配 — 复用 BT-006 已缓存申万一级行业指数 (2014-02 → 2026-07-31) + CSI300.

为什么用本地缓存: akshare 申万接口现被限速 (单指数 >10s, 31 个指数 6min+),
BT-006 (2026-08-04) 已抓取并落盘同一口径数据, 复用可避免重复网络请求且口径一致。
"""
import shutil
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
BT006 = BASE.parent / "BT-006" / "data"

CODES = ["801010", "801030", "801040", "801050", "801080", "801110", "801120",
         "801130", "801140", "801150", "801160", "801170", "801180", "801200",
         "801210", "801230", "801710", "801720", "801730", "801740", "801750",
         "801760", "801770", "801780", "801790", "801880", "801890", "801950",
         "801960", "801970", "801980"]

names = pd.read_csv(BT006 / "sw_l1_names.csv").set_index("code")["name"].to_dict()

frames = {}
for code in CODES:
    fp = BT006 / f"sw_l1_{code}.csv"
    if not fp.exists():
        print(f"  !! missing {code}")
        continue
    df = pd.read_csv(fp)
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "close"]].dropna().sort_values("date")
    label = f"{code}_{names.get(int(code), code)}"
    frames[label] = df.set_index("date")["close"]
    print(f"  {label}: {len(df)} bars ({df['date'].iloc[0].date()} → {df['date'].iloc[-1].date()})")

panel = pd.DataFrame(frames).sort_index()
panel.index.name = "date"
panel.to_csv(DATA / "sw_l1_close.csv")
print(f"\nSW panel: {panel.shape}  {panel.index[0].date()} → {panel.index[-1].date()}")
# 交集区间 (剔除早期缺列的行业): 取所有列都非 NaN 的起点
common_start = panel.dropna().index[0]
print(f"balanced start (all cols present): {common_start.date()}")

csi = pd.read_csv(BT006 / "csi300_daily.csv")
csi["date"] = pd.to_datetime(csi["date"])
csi = csi[["date", "close"]].dropna().sort_values("date")
csi.to_csv(DATA / "csi300_close.csv", index=False)
print(f"CSI300: {len(csi)} bars ({csi['date'].iloc[0].date()} → {csi['date'].iloc[-1].date()})")
