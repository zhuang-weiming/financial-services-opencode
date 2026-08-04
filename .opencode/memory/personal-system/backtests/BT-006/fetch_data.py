#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BT-006 数据抓取 — 券商集中度 vs 行业分散 量化检验
数据源: akshare (SW指数/汇率/乐咕估值/东财主营构成) + mootdx
样本: 2014-02 ~ 2026-08 (SW指数历史起点)
"""
import akshare as ak
import pandas as pd
import time, os, warnings, json
warnings.filterwarnings('ignore')

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)

def save(df, name):
    df.to_csv(os.path.join(OUT, name), index=False)
    print(f"  saved {name}: {df.shape}")

# ---------- 1. USDCNY 央行中间价 (2014-2026) ----------
print("[1] USDCNY ...")
fx = ak.currency_boc_sina(symbol="美元", start_date="20140101", end_date="20260804")
fx = fx.rename(columns={"日期": "date", "央行中间价": "mid"})
fx = fx[["date", "mid"]].dropna()
fx["mid"] = fx["mid"] / 100.0  # 央行中间价单位 ×100
save(fx, "usdcny_mid.csv")

# ---------- 2. SW L1 行业指数日线 ----------
print("[2] SW L1 ...")
l1 = ak.sw_index_first_info()
l1_map = {r["行业代码"].split(".")[0]: r["行业名称"] for _, r in l1.iterrows()}
l1_map = {k: v for k, v in l1_map.items() if k.isdigit()}
for code, name in l1_map.items():
    try:
        df = ak.index_hist_sw(symbol=code, period="day")
        df = df[["日期", "收盘"]].rename(columns={"日期": "date", "收盘": "close"})
        df["code"] = code
        save(df, f"sw_l1_{code}.csv")
        time.sleep(0.35)
    except Exception as e:
        print(f"  ERR {code} {name}: {str(e)[:80]}")
save(pd.DataFrame([{"code": k, "name": v} for k, v in l1_map.items()]), "sw_l1_names.csv")

# ---------- 3. SW L2 行业指数日线 (证券/保险/造纸/航空机场/航空装备/军工电子/化学制药/生物制品) ----------
print("[3] SW L2 ...")
l2 = ak.sw_index_second_info()
l2_focus = ["证券Ⅱ", "保险Ⅱ", "造纸", "航空机场", "航空装备Ⅱ", "军工电子Ⅱ", "化学制药", "生物制品", "白酒Ⅱ", "新能源"]
l2_sel = l2[l2["行业名称"].isin(l2_focus)]
l2_map = {}
for _, r in l2_sel.iterrows():
    code = r["行业代码"].split(".")[0]
    l2_map[code] = r["行业名称"]
    try:
        df = ak.index_hist_sw(symbol=code, period="day")
        df = df[["日期", "收盘"]].rename(columns={"日期": "date", "收盘": "close"})
        df["code"] = code
        save(df, f"sw_l2_{code}.csv")
        time.sleep(0.35)
    except Exception as e:
        print(f"  ERR {code} {r['行业名称']}: {str(e)[:80]}")
save(pd.DataFrame([{"code": k, "name": v} for k, v in l2_map.items()]), "sw_l2_names.csv")

# ---------- 4. 沪深300 日线 ----------
print("[4] CSI300 ...")
try:
    csi = ak.stock_zh_index_daily_em(symbol="sh000300")
    csi = csi.rename(columns={"date": "date", "close": "close"})
    csi = csi[["date", "close"]]
    save(csi, "csi300_daily.csv")
except Exception as e:
    print("  EM ERR:", str(e)[:120])
    from mootdx.quotes import Quotes
    client = Quotes.factory(market='std')
    df = client.index(symbol='000300', frequency=9, offset=0)
    df = df.rename(columns={'datetime': 'date', 'close': 'close'})
    save(df[['date', 'close']], "csi300_daily.csv")

# ---------- 5. 399975 券商指数日线 (mootdx 交叉验证) ----------
print("[5] 399975 ...")
try:
    from mootdx.quotes import Quotes
    client = Quotes.factory(market='std')
    df = client.index(symbol='399975', frequency=9, offset=0)
    df = df.rename(columns={'datetime': 'date', 'close': 'close'})
    df = df[['date', 'close']]
    save(df, "broker_idx_399975.csv")
except Exception as e:
    print("  mootdx 399975 ERR:", str(e)[:120])

# ---------- 6. 个股 PB/PE 历史 (乐咕) — 估值分位 ----------
print("[6] 个股估值 ...")
stocks = {
    # 券商
    "600030": "中信证券", "601688": "华泰证券", "601211": "国泰君安", "600999": "招商证券",
    "000776": "广发证券", "601377": "兴业证券", "601901": "方正证券", "601696": "中银证券",
    "601990": "南京证券", "000166": "申万宏源", "601066": "中信建投", "601995": "中金公司",
    # 保险
    "601318": "中国平安", "601628": "中国人寿", "601601": "中国太保", "601336": "新华保险", "601319": "中国人保",
    # 创新药
    "600276": "恒瑞医药", "603259": "药明康德", "688235": "百济神州", "688180": "君实生物",
    "688336": "荣昌生物", "688520": "神州细胞", "600196": "复星医药", "300347": "泰格医药",
    "002821": "凯莱英", "688506": "百利天恒",
    # 军工
    "600893": "航发动力", "000768": "中航西飞", "600760": "中航沈飞", "002179": "中航光电",
    "600862": "中航高科", "601989": "中国重工", "600150": "中国船舶", "600038": "中直股份",
    # 航空
    "601111": "中国国航", "600115": "东方航空", "600029": "南方航空", "601021": "春秋航空",
    "603885": "吉祥航空", "600009": "上海机场", "600004": "白云机场",
    # 造纸
    "000488": "晨鸣纸业", "002078": "太阳纸业", "600567": "山鹰国际", "600966": "博汇纸业",
    "603733": "仙鹤股份", "002521": "齐峰新材",
    # 新能源
    "300750": "宁德时代", "002594": "比亚迪", "601012": "隆基绿能", "600438": "通威股份",
    "300274": "阳光电源", "002459": "晶澳科技", "688599": "天合光能", "002129": "TCL中环",
    # 消费(白酒/食品)
    "600519": "贵州茅台", "000858": "五粮液", "000568": "泸州老窖", "600887": "伊利股份",
    "603288": "海天味业", "000895": "双汇发展", "600809": "山西汾酒",
}
meta = []
for code, name in stocks.items():
    try:
        df = ak.stock_a_indicator_lg(symbol=code)
        df = df[["trade_date", "pe", "pb"]].rename(columns={"trade_date": "date"})
        df["code"] = code
        df["name"] = name
        save(df, f"lg_{code}.csv")
        meta.append({"code": code, "name": name})
        time.sleep(0.4)
    except Exception as e:
        print(f"  ERR {code} {name}: {str(e)[:80]}")
save(pd.DataFrame(meta), "lg_stocks.csv")

# ---------- 7. 券商主营构成 (投行业务) ----------
print("[7] 主营构成 ...")
for code in ["SH600030", "SH601995", "SH601696", "SH601688", "SH601066"]:
    try:
        df = ak.stock_zygc_em(symbol=code)
        save(df, f"zygc_{code}.csv")
        time.sleep(0.5)
    except Exception as e:
        print(f"  ERR zygc {code}: {str(e)[:80]}")

print("DONE")
