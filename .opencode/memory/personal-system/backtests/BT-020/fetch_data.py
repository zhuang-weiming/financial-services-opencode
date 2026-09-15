#!/usr/bin/env python3
"""BT-020 数据抓取 — 申万一级行业指数 (31) + 沪深300 (regime 基准).

数据源: akshare `index_hist_sw` (申万宏源官方, 1999-12 起)
复权口径: 行业指数为**价格指数** (申万官方发布, 非全收益), 但行业指数不含分红除权跳空问题,
          口径为官方 index value; 下文所有 forward return 基于该收盘价, 无 lookahead。
"""
import time
from pathlib import Path

import akshare as ak
import pandas as pd

OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)

# 申万一级行业 (2021 版, 31 个)
SW_L1 = {
    "801010": "农林牧渔", "801030": "基础化工", "801040": "钢铁", "801050": "有色金属",
    "801080": "电子", "801110": "家用电器", "801120": "食品饮料", "801130": "纺织服饰",
    "801140": "轻工制造", "801150": "医药生物", "801160": "公用事业", "801170": "交通运输",
    "801180": "房地产", "801200": "商贸零售", "801210": "社会服务", "801230": "综合",
    "801710": "建筑材料", "801720": "建筑装饰", "801730": "电力设备", "801740": "国防军工",
    "801750": "计算机", "801760": "传媒", "801770": "通信", "801780": "银行",
    "801790": "非银金融", "801880": "汽车", "801890": "机械设备", "801950": "煤炭",
    "801960": "石油石化", "801970": "环保", "801980": "美容护理",
}


def fetch_sw():
    frames = {}
    for code, name in SW_L1.items():
        try:
            df = ak.index_hist_sw(symbol=code, period="day")
            df = df.rename(columns={"日期": "date", "收盘": "close"})
            df["date"] = pd.to_datetime(df["date"])
            df = df[["date", "close"]].dropna().sort_values("date")
            frames[f"{code}_{name}"] = df.set_index("date")["close"]
            print(f"  {code} {name}: {len(df)} bars ({df['date'].iloc[0].date()} → {df['date'].iloc[-1].date()})")
        except Exception as e:
            print(f"  !! {code} {name}: {e}")
        time.sleep(0.3)
    panel = pd.DataFrame(frames)
    panel.index.name = "date"
    panel.to_csv(OUT / "sw_l1_close.csv")
    print(f"saved SW panel: {panel.shape}")
    return panel


def fetch_csi300():
    try:
        df = ak.index_zh_a_hist(symbol="000300", period="daily",
                                start_date="20000101", end_date="20260930")
        df = df.rename(columns={"日期": "date", "收盘": "close"})
        df["date"] = pd.to_datetime(df["date"])
        df = df[["date", "close"]].dropna().sort_values("date")
        df.to_csv(OUT / "csi300_close.csv", index=False)
        print(f"saved CSI300: {len(df)} bars ({df['date'].iloc[0].date()} → {df['date'].iloc[-1].date()})")
    except Exception as e:
        print(f"CSI300 via index_zh_a_hist failed: {e}; trying stock_zh_index_daily_tx")
        df = ak.stock_zh_index_daily_tx(symbol="sh000300")
        df = df.rename(columns={"date": "date", "close": "close"})
        df["date"] = pd.to_datetime(df["date"])
        df = df[["date", "close"]].dropna().sort_values("date")
        df.to_csv(OUT / "csi300_close.csv", index=False)
        print(f"saved CSI300 (tx): {len(df)} bars")


if __name__ == "__main__":
    print("[1] 申万一级行业指数...")
    fetch_sw()
    print("[2] 沪深300...")
    fetch_csi300()
