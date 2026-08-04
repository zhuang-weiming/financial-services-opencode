#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BT-006 主分析 v2 — 券商集中度 vs 行业分散 量化检验
券商指数代理: 399975 中证全指证券公司 (2015-10起, 连续)
检验1: 人民币升值周期行业收益排名 (2015-2026)
检验2: 券商 vs 沪深300 beta / 分阶段胜率 (2016-2026)
检验3: 估值分位 (PB/PE, 2016-2026)
检验4: 集中度风险模拟 (暴跌窗口 -20%)
"""
import pandas as pd
import numpy as np
import os, json, warnings
warnings.filterwarnings('ignore')

BASE = "/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/backtests/BT-006"
DATA = os.path.join(BASE, "data")

def load(name):
    return pd.read_csv(os.path.join(DATA, name))

def monthly_ret(daily_close, name):
    df = daily_close.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")["close"].astype(float)
    m = df.resample("ME").last()
    ret = m.pct_change().dropna()
    ret.name = name
    return ret

# ---------- 面板 ----------
csi_m = monthly_ret(load("csi300_daily.csv"), "csi300")
sec_m = monthly_ret(load("broker_idx_399975.csv"), "sec")     # 399975 券商

l1_names = load("sw_l1_names.csv"); l1_map = dict(zip(l1_names["code"].astype(str), l1_names["name"]))
l1_panel = {}
for code in l1_map:
    try:
        d = load(f"sw_l1_{code}.csv")
        if len(d) > 200:
            l1_panel[code] = monthly_ret(d, code)
    except FileNotFoundError:
        pass
l1_panel = pd.concat(l1_panel, axis=1).dropna(how="all")

l2_names = load("sw_l2_names.csv"); l2_map = dict(zip(l2_names["code"].astype(str), l2_names["name"]))
l2_panel = {}
for code in l2_map:
    try:
        d = load(f"sw_l2_{code}.csv")
        if len(d) > 200:
            l2_panel[code] = monthly_ret(d, code)
    except FileNotFoundError:
        pass
l2_panel = pd.concat(l2_panel, axis=1).dropna(how="all")

# ---------- 检验1: 人民币升值周期 ----------
fx = load("usdcny_mid.csv"); fx["date"] = pd.to_datetime(fx["date"])
fx_m = fx.sort_values("date").set_index("date")["mid"].resample("ME").last()
fx_chg = fx_m.pct_change().dropna()
fx_chg = fx_chg.loc[fx_chg.index >= "2015-01-01"]
csi_m_a = csi_m.reindex(fx_chg.index).dropna()

appr = fx_chg < 0; depr = fx_chg > 0
print(f"[T1] {fx_chg.index[0].date()}~{fx_chg.index[-1].date()} {len(fx_chg)}月, 升值月{appr.sum()}({appr.mean():.1%}) 贬值月{int(depr.sum())}")
print(f"     USDCNY: {fx_m.loc['2015-01'].values[0]:.3f} -> {fx_m.loc['2026-07'].values[0]:.3f}")

def rank_table(panel, names, label, min_months=60):
    rows = []
    for code, r in panel.items():
        rr = pd.concat([r, csi_m_a], axis=1).dropna()
        if len(rr) < min_months:
            continue
        rr = rr.loc[rr.index >= "2015-01-01"]
        ret, mkt = rr.iloc[:, 0], rr.iloc[:, 1]
        exc = ret - mkt
        mask = fx_chg.reindex(rr.index)
        a, d = exc[mask < 0], exc[mask > 0]
        if len(a) < 10:
            continue
        maskv = mask.values[mask.notna().values & (mask != 0).values]
        excv = exc.values[mask.notna().values & (mask != 0).values]
        beta_fx = np.polyfit(-maskv, excv, 1)[0] if len(maskv) > 30 else np.nan
        rows.append({"行业": names.get(code, code), "代码": code,
                     "升值月均值超额%": a.mean() * 100, "贬值月均值超额%": d.mean() * 100,
                     "升贬差pp": (a.mean() - d.mean()) * 100,
                     "升值月胜率": (a > 0).mean(), "升值月数": len(a),
                     "FX敏感系数": beta_fx})
    t = pd.DataFrame(rows).sort_values("升值月均值超额%", ascending=False)
    print(f"\n=== {label} ===")
    print(t.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    return t

t1_l1 = rank_table(l1_panel, l1_map, "T1a: 申万一级 升值周期月度超额收益排名 (2015-2026)")

# L2 焦点 + 399975 券商
focus = {}
for code, name in l2_map.items():
    if name in ["证券Ⅱ", "保险Ⅱ", "造纸", "航空机场", "航空装备Ⅱ", "军工电子Ⅱ", "化学制药", "生物制品", "白酒Ⅱ"]:
        focus[code] = name
focus["399975"] = "证券(399975)"
sec_panel = l2_panel.copy()
sec_panel["399975"] = sec_m.reindex(sec_panel.index)
t1_l2 = rank_table(sec_panel[list(focus.keys())], focus, "T1b: 焦点行业/指数 升值周期 (2015-2026)", min_months=20)

# 稳健性 2017-2026
rows3 = []
for code, r in l1_panel.items():
    rr = pd.concat([r, csi_m_a], axis=1).dropna()
    rr = rr.loc[rr.index >= "2017-01-01"]
    if len(rr) < 60:
        continue
    exc = rr.iloc[:, 0] - rr.iloc[:, 1]
    mask = fx_chg.reindex(rr.index)
    a, d = exc[mask < 0], exc[mask > 0]
    if len(a) < 10:
        continue
    rows3.append({"行业": l1_map[code], "升贬差pp": (a.mean() - d.mean()) * 100,
                  "升值月均值超额%": a.mean() * 100, "贬值月均值超额%": d.mean() * 100,
                  "升值月数": len(a)})
t1b = pd.DataFrame(rows3).sort_values("升贬差pp", ascending=False)
print("\n=== T1c: 稳健性 2017-2026 (升贬差排名) ===")
print(t1b.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

t1 = {
    "n_months": int(len(fx_chg)), "n_appr": int(appr.sum()), "n_depr": int(depr.sum()),
    "usdcny_2015_2026": [float(fx_m.loc["2015-01"].values[0]), float(fx_m.loc["2026-07"].values[0])],
    "l1_rank": t1_l1[["行业", "升值月均值超额%", "升贬差pp", "升值月胜率", "FX敏感系数"]].to_dict("records"),
    "l2_rank": t1_l2[["行业", "升值月均值超额%", "升贬差pp", "升值月胜率"]].to_dict("records"),
    "l1_2017_rank": t1b.to_dict("records"),
}

# ---------- 检验2: 券商 vs 沪深300 ----------
pair = pd.concat([sec_m, csi_m], axis=1).dropna()
pair.columns = ["sec", "csi"]
pair = pair.loc[pair.index >= "2016-01-01"]

beta = np.cov(pair["sec"], pair["csi"])[0, 1] / np.var(pair["csi"])
alpha_m = pair["sec"].mean() - beta * pair["csi"].mean()
r2 = np.corrcoef(pair["sec"], pair["csi"])[0, 1] ** 2
cum_exc = np.log1p(pair["sec"]).sum() - np.log1p(pair["csi"]).sum()
n_years = len(pair) / 12
ann_exc = (np.exp(cum_exc) ** (1 / n_years) - 1) * 100

t12 = pair["csi"].rolling(12).apply(lambda x: np.prod(1 + x) - 1)
regime = pd.Series("震荡", index=pair.index)
regime[t12 > 0.15] = "牛市"
regime[t12 < -0.10] = "熊市"
pair["regime"] = regime

reg_stats = []
for r in ["牛市", "震荡", "熊市"]:
    sub = pair[pair["regime"] == r]
    if len(sub) == 0:
        continue
    reg_stats.append({
        "阶段": r, "月数": len(sub),
        "券商月均%": sub["sec"].mean() * 100, "300月均%": sub["csi"].mean() * 100,
        "月度超额pp": (sub["sec"] - sub["csi"]).mean() * 100,
        "跑赢胜率": (sub["sec"] > sub["csi"]).mean(),
        "阶段累计超额%": (np.prod(1 + sub["sec"]) / np.prod(1 + sub["csi"]) - 1) * 100,
    })
t2_reg = pd.DataFrame(reg_stats)
print("\n=== T2a: 券商(399975) vs 沪深300 分阶段统计 2016-2026 ===")
print(t2_reg.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

roll_beta = pair["sec"].rolling(36).cov(pair["csi"]) / pair["csi"].rolling(36).var()
print("\n=== T2b: 滚动36月beta (年末) ===")
print(roll_beta.resample("YE").last().dropna().to_string(float_format=lambda x: f"{x:.2f}"))

yearly = pair.groupby(pair.index.year).apply(
    lambda g: pd.Series({"券商%": (np.prod(1 + g["sec"]) - 1) * 100,
                         "300%": (np.prod(1 + g["csi"]) - 1) * 100,
                         "超额pp": (np.prod(1 + g["sec"]) / np.prod(1 + g["csi"]) - 1) * 100,
                         "跑赢月数": int((g["sec"] > g["csi"]).sum())}))
print("\n=== T2c: 年度收益对比 ===")
print(yearly.to_string(float_format=lambda x: f"{x:.1f}"))
print(f"\n[T2d] beta={beta:.2f} alpha_monthly={alpha_m*100:.2f}% R²={r2:.2f} 累计对数超额={cum_exc:.3f} 年化超额={ann_exc:.2f}%")

t2 = {
    "beta": beta, "alpha_monthly_pct": alpha_m * 100, "r2": r2,
    "cum_exc_log": float(cum_exc), "ann_exc_pct": ann_exc, "n_months": int(len(pair)),
    "regime": reg_stats,
    "rolling_beta": {str(k.date()): round(v, 2) for k, v in roll_beta.resample("YE").last().dropna().items()},
    "yearly": {str(k): v.to_dict() for k, v in yearly.items()},
}

# ---------- 检验3: 估值分位 ----------
sectors = {
    "券商": ["600030", "601688", "601211", "600999", "000776", "601377", "601901", "601696", "601990", "000166", "601066", "601995"],
    "保险": ["601318", "601628", "601601", "601336", "601319"],
    "创新药": ["600276", "603259", "688235", "688180", "688336", "688520", "600196", "300347", "002821", "688506"],
    "军工": ["600893", "000768", "600760", "002179", "600862", "601989", "600150", "600038"],
    "航空": ["601111", "600115", "600029", "601021", "603885", "600009", "600004"],
    "造纸": ["000488", "002078", "600567", "600966", "603733", "002521"],
    "新能源": ["300750", "002594", "601012", "600438", "300274", "002459", "688599", "002129"],
    "消费": ["600519", "000858", "000568", "600887", "603288", "000895", "600809"],
}

def percentile_series(s):
    s = s.dropna()
    if len(s) < 60:
        return np.nan
    return (s <= s.iloc[-1]).mean() * 100

def get_stock(code):
    d = pd.read_csv(os.path.join(DATA, f"bs_{code}.csv"))
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date").set_index("date")
    for col in ["peTTM", "pbMRQ", "close"]:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    return d

results3, stock_detail = [], []
for sec_name, codes in sectors.items():
    pb10, pe10, pb5, pe5, pb_n, pe_n = [], [], [], [], [], []
    for code in codes:
        try:
            d = get_stock(code)
        except FileNotFoundError:
            continue
        if len(d) < 60:
            continue
        h10 = d.loc[d.index >= "2016-01-01"]
        h5 = d.loc[d.index >= "2021-01-01"]
        p10 = percentile_series(h10["pbMRQ"])
        e10 = percentile_series(h10["peTTM"].where(h10["peTTM"] > 0))
        p5 = percentile_series(h5["pbMRQ"])
        e5 = percentile_series(h5["peTTM"].where(h5["peTTM"] > 0))
        pb10.append(p10); pe10.append(e10); pb5.append(p5); pe5.append(e5)
        pb_n.append(d["pbMRQ"].iloc[-1]); pe_n.append(d["peTTM"].where(d["peTTM"] > 0).iloc[-1])
        stock_detail.append({"板块": sec_name, "代码": code, "PB分位10y%": p10, "PE分位10y%": e10,
                             "PB分位5y%": p5, "PE分位5y%": e5, "当前PB": d["pbMRQ"].iloc[-1],
                             "当前PE_TTM": d["peTTM"].where(d["peTTM"] > 0).iloc[-1]})
    results3.append({
        "板块": sec_name, "样本": len(pb_n),
        "PB中位": round(float(np.nanmedian(pb_n)), 2), "PB分位10Y%": round(float(np.nanmedian(pb10)), 0),
        "PB分位5Y%": round(float(np.nanmedian(pb5)), 0),
        "PE中位": round(float(np.nanmedian(pe_n)), 1), "PE分位10Y%": round(float(np.nanmedian(pe10)), 0),
        "PE分位5Y%": round(float(np.nanmedian(pe5)), 0),
    })
t3 = pd.DataFrame(results3).sort_values("PB分位10Y%")
print("\n=== T3: 板块估值分位 (成分股中位, 2016-2026) ===")
print(t3.to_string(index=False))
pd.DataFrame(stock_detail).to_csv(os.path.join(BASE, "t3_stock_detail.csv"), index=False)

# ---------- 检验4: 集中度风险 ----------
px = pd.concat([
    sec_m.rename("券商"),
    l2_panel["801194"].rename("保险"),
    l2_panel["801151"].rename("化学制药"),
    csi_m.rename("沪深300"),
], axis=1).dropna()
px = px.loc[px.index >= "2016-01-01"]

betas, betas_r, vols = {}, {}, {}
for col in ["券商", "保险", "化学制药"]:
    betas[col] = np.cov(px[col], px["沪深300"])[0, 1] / np.var(px["沪深300"])
    recent = px.loc[px.index >= "2023-01-01"]
    betas_r[col] = np.cov(recent[col], recent["沪深300"])[0, 1] / np.var(recent["沪深300"])
    vols[col] = px[col].std() * np.sqrt(12) * 100
print("\n=== T4a: Beta & 年化波动 (月度) ===")
for col in ["券商", "保险", "化学制药"]:
    print(f"  {col}: beta(16-26)={betas[col]:.2f}  beta(23-26)={betas_r[col]:.2f}  年化波动={vols[col]:.1f}%")
print(f"  沪深300年化波动: {px['沪深300'].std()*np.sqrt(12)*100:.1f}%")
print("  相关系数:\n", px[["券商", "保险", "化学制药", "沪深300"]].corr().round(2).to_string())

combos = {
    "A: 券商50%+现金50%": {"券商": 0.5},
    "B: 券商30%+保险10%+化学制药10%": {"券商": 0.3, "保险": 0.1, "化学制药": 0.1},
    "C: 沪深300 50%+现金50%": {"沪深300": 0.5},
}
print("\n=== T4b: 组合统计 (2016-2026月度) ===")
rows4 = []
for name, w in combos.items():
    cols = [c for c in w]
    r = sum(w[c] * px[c] for c in cols)
    # 沪深300 自身 beta=1.0
    pbeta = sum(w[c] * (betas.get(c, 1.0)) for c in cols)
    pbeta_r = sum(w[c] * (betas_r.get(c, 1.0)) for c in cols)
    vol_ann = r.std() * np.sqrt(12) * 100
    r3 = r.rolling(3).apply(lambda x: np.prod(1 + x) - 1, raw=True)
    rows4.append({
        "组合": name, "beta(23-26)": round(pbeta_r, 2), "beta(16-26)": round(pbeta, 2),
        "年化波动%": round(vol_ann, 1),
        "300暴跌-20%损失%(近beta)": round(-20 * pbeta_r, 1),
        "300暴跌-20%损失%(全期beta)": round(-20 * pbeta, 1),
        "历史3月收益5%分位%": round(r3.quantile(0.05) * 100, 1),
        "历史最差3月%": round(r3.min() * 100, 1),
    })
t4 = pd.DataFrame(rows4)
print(t4.to_string(index=False))

sec_worst = px["券商"].rolling(3).apply(lambda x: np.prod(1 + x) - 1, raw=True)
csi_worst = px["沪深300"].rolling(3).apply(lambda x: np.prod(1 + x) - 1, raw=True)
print(f"\n  券商历史最差3月: {sec_worst.min()*100:.1f}% ({sec_worst.idxmin().date()})")
print(f"  沪深300历史最差3月: {csi_worst.min()*100:.1f}% ({csi_worst.idxmin().date()})")
# 若300单月-20%情景(历史未发生, 用beta×-20%):
print(f"  若沪深300月线-20%(压力情景): 券商beta效应 {betas['券商']*20:.0f}% 实际历史上限参考最差单月 {px['券商'].min()*100:.1f}%")

# ---------- 保存 ----------
out = {
    "t1": t1, "t2": t2,
    "t3": t3.to_dict("records"),
    "t4": rows4,
    "t4_betas": {k: round(v, 3) for k, v in betas.items()},
    "t4_betas_recent": {k: round(v, 3) for k, v in betas_r.items()},
    "corr": px[["券商", "保险", "化学制药", "沪深300"]].corr().round(3).to_dict(),
    "sec_worst_3m": (round(float(sec_worst.min() * 100), 1), str(sec_worst.idxmin().date())),
    "csi_worst_3m": (round(float(csi_worst.min() * 100), 1), str(csi_worst.idxmin().date())),
}
with open(os.path.join(BASE, "results.json"), "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("\nSAVED results.json")
