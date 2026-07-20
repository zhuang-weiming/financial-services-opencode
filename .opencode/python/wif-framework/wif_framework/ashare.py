from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

_env_path = os.environ.get("WIF_ASHARE_DATA_DIR", "")
DEFAULT_DATA_DIR = (
    Path(_env_path).expanduser().resolve() if _env_path
    else Path(__file__).resolve().parents[4] / "example" / "wif-ashare" / "data"
)

TECH_START = pd.Timestamp("2019-01-01")
CHIP_START = pd.Timestamp("2022-11-01")
COST = 0.003
TROUGH_THETA = 0.10

TREND_UP = 0.07
TREND_DOWN = -0.07

PMI_MIN, PMI_RANGE = 47.0, 6.0
M2_MIN, M2_RANGE = 6.0, 9.0
MCI_Q1_THRESH = 0.53
MCI_Q3_THRESH = 0.47


def pmi_norm(v: float) -> float:
    return max(0.0, min(1.0, (v - PMI_MIN) / PMI_RANGE))


def m2_norm(v: float) -> float:
    return max(0.0, min(1.0, (v - M2_MIN) / M2_RANGE))


def compute_mci(pmi: float, m2: float) -> float:
    return 0.5 * pmi_norm(pmi) + 0.5 * m2_norm(m2)


def mci_to_quadrant(mci: float) -> int:
    if mci >= MCI_Q1_THRESH:
        return 1
    if mci <= MCI_Q3_THRESH:
        return 3
    return 2


def normalize_weights(w: dict[str, float]) -> dict[str, float]:
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


def make_qw():
    qw = {
        1: normalize_weights({"hs300": 0.80, "cyb": 0.20, "gold": 0.10, "bond": 0.00}),
        2: normalize_weights({"hs300": 0.60, "cyb": 0.15, "gold": 0.25, "bond": 0.10}),
        3: normalize_weights({"hs300": 0.45, "cyb": 0.10, "gold": 0.25, "bond": 0.15, "cash": 0.05}),
    }
    out = {}
    for q, w in qw.items():
        w2 = w.copy()
        hs = w2.pop("hs300")
        csi = round(hs * 0.30, 4)
        w2["hs300"] = round(hs - csi, 4)
        w2["csi500"] = csi
        out[q] = w2
    return out


QW = make_qw()

EM_WEIGHTS = {
    "L1": normalize_weights({"hs300": 0.15, "gold": 0.30, "bond": 0.25, "cash": 0.30}),
    "L2": normalize_weights({"hs300": 0.10, "gold": 0.60, "bond": 0.10, "cash": 0.20}),
    "L3": normalize_weights({"hs300": 0.05, "gold": 0.70, "bond": 0.05, "cash": 0.20}),
}


def get_em_weight(r20: float):
    if r20 < -0.20:
        return "L3", EM_WEIGHTS["L3"]
    if r20 < -0.12:
        return "L2", EM_WEIGHTS["L2"]
    if r20 < -0.08:
        return "L1", EM_WEIGHTS["L1"]
    return None, None


def effective_quadrant(mci_q: int, trend: float) -> int:
    if trend > TREND_UP:
        return 1
    if trend < TREND_DOWN:
        return 3
    return mci_q


def apply_tech_replacement(w: dict[str, float], effective_q: int, date: pd.Timestamp, has_chip: bool) -> dict[str, float]:
    w = w.copy()
    if "tech399" not in w:
        extra = 0.08 if effective_q == 1 else (0.05 if effective_q == 2 else 0.03)
        cyb_key = "cyb"
        if cyb_key not in w:
            return w
        w["tech399"] = extra
        w[cyb_key] = max(0, w.get(cyb_key, 0) - extra)
    if has_chip and date >= CHIP_START:
        if w.get("tech399", 0) > 0:
            w["chip_frac"] = 0.50
    return w


def calc_portfolio_return(pw: dict, r: pd.Series, use_chip: bool) -> float:
    ret = 0.0
    for asset in ["hs300", "cyb", "gold", "bond"]:
        col = f"{asset}_ret"
        rv = r.get(col) if pd.notna(r.get(col)) else 0.0
        ret += pw.get(asset, 0) * (rv if rv is not None else 0.0)
    if pw.get("csi500", 0) > 0:
        csi_rv = r.get("csi500_ret") if pd.notna(r.get("csi500_ret")) else r.get("hs300_ret", 0)
        ret += pw["csi500"] * (csi_rv if csi_rv is not None else 0.0)
    if pw.get("tech399", 0) > 0:
        if use_chip and pw.get("chip_frac", 0) > 0 and pd.notna(r.get("chip_ret")):
            rv_399 = r.get("tech_ret") if pd.notna(r.get("tech_ret")) else r.get("cyb_ret", 0)
            rv_chip = r.get("chip_ret", 0)
            rv_tech = rv_399 * (1 - pw["chip_frac"]) + rv_chip * pw["chip_frac"]
        else:
            rv_tech = r.get("tech_ret") if pd.notna(r.get("tech_ret")) else r.get("cyb_ret", 0)
        ret += pw["tech399"] * (rv_tech if rv_tech is not None else 0.0)
    return ret


def load_data(data_dir: Optional[Path] = None) -> pd.DataFrame:
    base = data_dir or DEFAULT_DATA_DIR
    etf = pd.read_csv(base / "etf_prices_new.csv", parse_dates=["Date"])
    etf = etf.sort_values("Date").reset_index(drop=True)
    if etf["cyb"].isna().any():
        etf["cyb"] = etf["cyb"].interpolate(method="linear")

    idx500 = pd.read_csv(base / "index_csi500_daily.csv", parse_dates=["date"])
    idx500 = idx500.sort_values("date").reset_index(drop=True)
    idx500["csi500_ret"] = idx500["close"].pct_change()
    idx500["csi500_price"] = idx500["close"]

    idx_tech = pd.read_csv(base / "index_tech_399303_daily.csv", parse_dates=["date"])
    idx_tech = idx_tech.sort_values("date").reset_index(drop=True)
    idx_tech["tech_ret"] = idx_tech["close"].pct_change()
    idx_tech["tech_price"] = idx_tech["close"]

    etf["YM"] = etf["Date"].dt.to_period("M").dt.to_timestamp().dt.strftime("%Y-%m")
    for c in ["hs300", "cyb", "gold", "bond"]:
        etf[f"{c}_ret"] = etf[c].pct_change()
    etf = pd.merge(etf, idx500[["date", "csi500_ret", "csi500_price"]].rename(columns={"date": "Date"}), on="Date", how="left")
    etf = pd.merge(etf, idx_tech[["date", "tech_ret", "tech_price"]].rename(columns={"date": "Date"}), on="Date", how="left")
    etf["R20"] = etf["hs300"].pct_change(20)
    etf["MA60"] = etf["hs300"].rolling(60).mean()
    etf["trend"] = etf["hs300"] / etf["MA60"] - 1
    etf["Year"] = etf["Date"].dt.year

    chip_path = base / "macro_chip_daily.csv"
    if chip_path.exists():
        chip_df = pd.read_csv(chip_path)
        chip_ym = dict(zip(chip_df["YM"], chip_df["cyb_chip_ret"]))
        chip_nav_cum = 1.0
        chip_nav_by_eom = {}
        for ym in sorted(chip_ym.keys()):
            chip_nav_cum *= (1 + chip_ym[ym])
            chip_nav_by_eom[ym] = chip_nav_cum
        chip_dates = []
        chip_navs = []
        for ym_str in sorted(chip_ym.keys()):
            mask = etf["YM"] == ym_str
            if not mask.any():
                continue
            chip_dates.append(etf.loc[mask, "Date"].iloc[-1])
            chip_navs.append(chip_nav_by_eom[ym_str])
        bom_mask = etf["YM"] == "2022-10"
        if bom_mask.any():
            bom_date = etf.loc[bom_mask, "Date"].iloc[-1]
            chip_nav_series = pd.Series([1.0] + chip_navs, index=[bom_date] + chip_dates).sort_index()
        else:
            chip_nav_series = pd.Series(chip_navs, index=chip_dates).sort_index()
        all_dates = etf.set_index("Date").index
        chip_reindexed = chip_nav_series.reindex(chip_nav_series.index.union(all_dates)).interpolate(method="time")
        etf["chip_nav"] = chip_reindexed.reindex(all_dates).values
        etf["chip_ret"] = etf["chip_nav"].pct_change()
    else:
        etf["chip_ret"] = np.nan

    macro_pmi = pd.read_csv(base / "macro_pmi.csv", parse_dates=["月份"])
    macro_m2 = pd.read_csv(base / "macro_m2_m1_spread.csv", parse_dates=["月份"])
    macro_pmi["YM"] = macro_pmi["月份"].dt.strftime("%Y-%m")
    macro_m2["YM"] = macro_m2["月份"].dt.strftime("%Y-%m")
    pmi_dict = dict(zip(macro_pmi["YM"], macro_pmi["PMI"]))
    m2_dict = dict(zip(macro_m2["YM"], macro_m2["M2_YoY"]))

    lp, lm = 50.0, 10.0
    for i in range(len(etf)):
        ym = etf.loc[i, "YM"]
        if ym in pmi_dict:
            lp = pmi_dict[ym]
        if ym in m2_dict:
            lm = m2_dict[ym]
        etf.loc[i, "PMI"] = lp
        etf.loc[i, "M2"] = lm

    etf["MCI"] = etf.apply(lambda r: compute_mci(r["PMI"], r["M2"]), axis=1)
    etf["Q"] = etf["MCI"].apply(mci_to_quadrant)

    return etf


BacktestResult = dict


def run_backtest(data_dir: Optional[Path] = None) -> BacktestResult:
    etf = load_data(data_dir)
    has_chip_data = "chip_ret" in etf.columns and etf["chip_ret"].notna().any()

    nav = 1.0
    pw = None
    prev_period = None
    navs = []
    em_lvs = []
    mcis = []
    qs = []
    eff_qs = []
    rebal_count = 0
    total_turnover = 0.0
    em_active = False
    em_trough_r20 = 0.0
    trend_up_days = 0
    trend_dn_days = 0
    override_q1_days = 0
    override_q3_days = 0

    for i in range(1, len(etf)):
        r = etf.iloc[i]
        mci = float(r["MCI"])
        q = int(r["Q"])
        r20 = float(r["R20"]) if pd.notna(r.get("R20")) else 0.0
        trend = float(r["trend"]) if pd.notna(r.get("trend")) else 0.0
        use_tech_now = bool(r["Date"] >= TECH_START and pd.notna(r.get("tech_ret")))
        use_chip_now = bool(has_chip_data and r["Date"] >= CHIP_START and pd.notna(r.get("chip_ret")))

        em_lv, em_w = get_em_weight(r20)
        is_em = em_lv is not None
        if is_em:
            if not em_active:
                em_active = True
                em_trough_r20 = r20
            else:
                em_trough_r20 = min(em_trough_r20, r20)
                if r20 > em_trough_r20 + TROUGH_THETA:
                    em_active = False
                    em_lv = None
                    em_w = None
        elif not is_em and em_active:
            if r20 > -0.08:
                em_active = False
        is_em = em_lv is not None

        cur_period = r["Date"].strftime("%Y-%m-%d")
        do_rebal = cur_period != prev_period

        if is_em:
            w = em_w
            effective_q = 0
        else:
            effective_q = effective_quadrant(q, trend)
            if trend > TREND_UP:
                trend_up_days += 1
                if q != 1:
                    override_q1_days += 1
            elif trend < TREND_DOWN:
                trend_dn_days += 1
                if q != 3:
                    override_q3_days += 1

            w_base = QW[effective_q].copy()
            if use_tech_now:
                extra = 0.08 if effective_q == 1 else (0.05 if effective_q == 2 else 0.03)
                w_base["cyb"] = max(0, w_base.get("cyb", 0) - extra)
                w_base["tech399"] = extra
            w = w_base

        if do_rebal:
            if pw is not None and not is_em:
                turn = sum(abs(w.get(k, 0) - pw.get(k, 0)) for k in set(w) | set(pw))
                total_turnover += turn
                nav *= (1 - turn * COST)
                if turn > 0.001:
                    rebal_count += 1
            pw = w
            prev_period = cur_period
        if pw is None:
            pw = w

        pr = calc_portfolio_return(pw, r, use_chip=use_chip_now)
        nav *= (1 + pr)
        navs.append(nav)
        em_lvs.append(em_lv or "N")
        mcis.append(mci)
        qs.append(q)
        eff_qs.append(effective_q)

    stats = _calc_stats(navs)
    return {
        "nav_series": navs,
        "stats": stats,
        "rebal_count": rebal_count,
        "total_turnover": total_turnover,
        "diagnostics": {
            "trend_up_days": trend_up_days,
            "trend_dn_days": trend_dn_days,
            "override_q1_days": override_q1_days,
            "override_q3_days": override_q3_days,
        },
        "em_lvs": em_lvs,
        "mcis": mcis,
        "qs": qs,
        "eff_qs": eff_qs,
    }


def _calc_stats(navs):
    n = np.array(navs)
    rets = np.concatenate([[0.0], np.diff(n) / n[:-1]])
    cum = n[-1] / n[0] - 1
    ny = len(n) / 252
    geo = (n[-1] / n[0]) ** (1.0 / ny) - 1 if ny > 0 else 0.0
    vol = rets.std() * np.sqrt(252)
    shp = geo / vol if vol > 1e-10 else 0.0
    dd = (n - np.maximum.accumulate(n)) / np.maximum.accumulate(n)
    mdd = dd.min()
    win = (rets[1:] > 0).mean()
    return {
        "cumulative": round(cum * 100, 1),
        "geo_cagr": round(geo * 100, 2),
        "volatility": round(vol * 100, 2),
        "sharpe": round(shp, 3),
        "mdd": round(mdd * 100, 1),
        "win_rate": round(win * 100, 1),
        "nav_end": round(n[-1], 4),
    }
