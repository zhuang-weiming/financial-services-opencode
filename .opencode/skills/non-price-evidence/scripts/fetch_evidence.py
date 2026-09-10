#!/usr/bin/env python3
"""
fetch_evidence.py — 非价格证据采集器 (non-price-evidence skill)

四个维度（全部为已验证可用的 Python 直连源）：
  1. 成交量结构  volume_structure   — 腾讯 OHLCV 计算 (换手/量比/OBV/AD/量价分布)
  2. 资金流向    fund_flow          — 东财 datacenter (两融/股东户数/龙虎榜/大宗/解禁/北向)
  3. 基本面      fundamentals       — 东财 datacenter (财务指标/一致预期)
  4. 宏观        macro              — akshare (中国 CPI/PPI/M2/社融)

设计原则：
  - 每个数据源独立 try/except，单点失败不中断整体
  - 输出含「数据新鲜度」+「缺口标注」+「与价格算法的交叉验证提示」
  - MCP 专属源 (llmquant-data macro/13F/SEC, Morningstar) 不在脚本内 —— 由 agent 调用，见 SKILL.md

用法:
    python3 fetch_evidence.py --code 601788 --market sh
    python3 fetch_evidence.py --code 601788 --market sh --dimensions volume,fund
    python3 fetch_evidence.py --code 601788 --json-out /tmp/evidence.json
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests

H = {"User-Agent": "Mozilla/5.0"}
EM_DC = "https://datacenter-web.eastmoney.com/api/data/v1/get"
EM_PUSH2 = "https://push2.eastmoney.com/api/qt/stock/get"
TX_KLINE = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"


def _try(fn, *a, **kw):
    """执行并捕获异常，返回 (ok, value_or_error)。"""
    try:
        return True, fn(*a, **kw)
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:100]}"


# ============================================================================
# 数据获取原语
# ============================================================================

def tx_kline(code: str, market: str, start: str, end: str) -> pd.DataFrame:
    """腾讯日线 (qfq 前复权)。"""
    sym = f"{market}{code}"
    r = requests.get(TX_KLINE, params={"param": f"{sym},day,{start},{end},2000,qfq"},
                     timeout=25, headers=H)
    d = r.json()["data"][sym]
    key = "qfqday" if "qfqday" in d else "day"
    df = pd.DataFrame([x[:6] for x in d[key]],
                      columns=["date", "open", "close", "high", "low", "volume"])
    for c in ["open", "close", "high", "low", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def em_datacenter(report: str, filt: str, sort_col: str, page_size: int = 5) -> list:
    """东财 datacenter-web 通用查询。"""
    r = requests.get(EM_DC, params={
        "reportName": report, "columns": "ALL", "filter": filt,
        "pageNumber": "1", "pageSize": str(page_size),
        "sortColumns": sort_col, "sortTypes": "-1"}, timeout=20, headers=H)
    d = r.json()
    if d.get("result") and d["result"].get("data"):
        return d["result"]["data"]
    raise RuntimeError(d.get("message", "no data"))


def em_secid(code: str, market: str) -> str:
    if market == "sh":
        return f"1.{code}"
    if market == "sz":
        return f"0.{code}"
    return f"1.{code}"


# ============================================================================
# 维度 1: 成交量结构
# ============================================================================

def dim_volume_structure(code: str, market: str) -> dict:
    out = {"dimension": "volume_structure", "status": "ok", "readings": {}, "gaps": []}
    end = datetime.today().strftime("%Y-%m-%d")
    start = (datetime.today() - timedelta(days=500)).strftime("%Y-%m-%d")
    ok, df = _try(tx_kline, code, market, start, end)
    if not ok:
        out["status"] = "fail"
        out["error"] = df
        return out
    C, V, H_, L = df["close"], df["volume"], df["high"], df["low"]

    # 量能趋势
    v5, v20, v60 = V.tail(5).mean(), V.tail(20).mean(), V.tail(60).mean()
    out["readings"]["volume_ratio_20_60"] = round(float(v20 / v60), 2)
    out["readings"]["volume_trend"] = "放量" if v20 > v60 * 1.1 else ("缩量" if v20 < v60 * 0.9 else "平量")

    # 量价配合 (OBV)
    obv = (np.sign(C.diff()) * V).fillna(0).cumsum()
    out["readings"]["obv_20d_slope"] = round(float(obv.diff(20).iloc[-1] / 1e6), 1)
    out["readings"]["obv_price_divergence"] = (
        "量价同向" if np.sign(obv.diff(20).iloc[-1]) == np.sign(C.diff(20).iloc[-1]) else "量价背离 ⚠️")

    # AD Line (上涨日/下跌日成交量累计)
    ad = ((2 * C - L - H_) / (H_ - L).replace(0, np.nan) * V).fillna(0).cumsum()
    out["readings"]["ad_line_20d_slope"] = round(float(ad.diff(20).iloc[-1] / 1e6), 1)

    # 量价分布 (近 60 日)
    up = C.diff() > 0
    up_vol = V[up].tail(60).sum()
    dn_vol = V[~up].tail(60).sum()
    out["readings"]["updown_volume_ratio"] = round(float(up_vol / dn_vol), 2) if dn_vol else None

    # 波动
    r = C.pct_change()
    out["readings"]["vol_60d_annualized"] = round(float(r.tail(60).std() * np.sqrt(252) * 100), 1)
    out["readings"]["price_vs_ma20"] = round(float((C.iloc[-1] / C.tail(20).mean() - 1) * 100), 1)
    out["readings"]["last_close"] = round(float(C.iloc[-1]), 2)
    out["readings"]["last_date"] = str(df["date"].iloc[-1].date())

    # 缺口
    out["gaps"].append("逐笔/Level2 十档 — 需付费 (QVeris/券商API)")
    out["gaps"].append("换手率 — 需流通股本 (东财 push2 可补, 当前未接入)")
    return out


# ============================================================================
# 维度 2: 资金流向
# ============================================================================

def dim_fund_flow(code: str, market: str) -> dict:
    out = {"dimension": "fund_flow", "status": "ok", "readings": {}, "gaps": [], "sources": {}}

    # 两融
    ok, d = _try(em_datacenter, "RPTA_WEB_RZRQ_GGMX", f'(SCODE="{code}")', "DATE", 5)
    if ok and d:
        latest = d[0]
        out["sources"]["margin"] = "✅ 东财"
        out["readings"]["margin_balance_yi"] = round(float(latest.get("RZYE", 0)) / 1e8, 2)
        out["readings"]["margin_date"] = str(latest.get("DATE", ""))[:10]
        if len(d) >= 5:
            chg = float(d[0].get("RZYE", 0)) - float(d[-1].get("RZYE", 0))
            out["readings"]["margin_5d_change_yi"] = round(chg / 1e8, 2)
    else:
        out["sources"]["margin"] = f"❌ {d}"

    # 股东户数
    ok, d = _try(em_datacenter, "RPT_HOLDERNUMLATEST", f'(SECURITY_CODE="{code}")', "END_DATE", 3)
    if ok and d:
        latest = d[0]
        out["sources"]["holder_count"] = "✅ 东财"
        out["readings"]["holder_count"] = latest.get("HOLDER_NUM")
        out["readings"]["holder_count_chg_pct"] = latest.get("HOLDER_NUM_RATIO")
        out["readings"]["holder_period"] = str(latest.get("END_DATE", ""))[:10]
    else:
        out["sources"]["holder_count"] = f"❌ {d}"

    # 龙虎榜 (近 30 日)
    since = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    ok, d = _try(em_datacenter, "RPT_DAILYBILLBOARD_DETAILSNEW",
                 f"(TRADE_DATE>='{since}')(SECURITY_CODE=\"{code}\")", "TRADE_DATE", 5)
    if ok and d:
        out["sources"]["dragon_tiger"] = f"✅ 东财 ({len(d)} 次上榜)"
        out["readings"]["dragon_tiger_events"] = [
            {"date": str(x.get("TRADE_DATE", ""))[:10], "explain": x.get("EXPLAIN")} for x in d[:3]]
    else:
        out["sources"]["dragon_tiger"] = f"⚠️ 近30日无上榜或 {d}"

    # 大宗交易
    ok, d = _try(em_datacenter, "RPT_DATA_BLOCKTRADE", f'(SECURITY_CODE="{code}")', "TRADE_DATE", 3)
    if ok and d:
        out["sources"]["block_trade"] = "✅ 东财"
        out["readings"]["block_trades"] = [
            {"date": str(x.get("TRADE_DATE", ""))[:10],
             "price": x.get("DEAL_PRICE"), "vol": x.get("DEAL_VOLUME"),
             "premium": x.get("PREMIUM_RATIO")} for x in d[:3]]
    else:
        out["sources"]["block_trade"] = f"⚠️ {d}"

    # 限售解禁
    ok, d = _try(em_datacenter, "RPT_LIFT_STAGE", f'(SECURITY_CODE="{code}")', "FREE_DATE", 3)
    if ok and d:
        out["sources"]["lockup"] = "✅ 东财"
        out["readings"]["lockup_upcoming"] = [
            {"date": str(x.get("FREE_DATE", ""))[:10], "shares": x.get("CURRENT_FREE_SHARES"),
             "ratio": x.get("FREE_RATIO")} for x in d[:3]]
    else:
        out["sources"]["lockup"] = f"⚠️ {d}"

    # 北向持股
    ok, d = _try(em_datacenter, "RPT_MUTUAL_HOLDSTOCKNORTH_STA", f'(SECURITY_CODE="{code}")', "TRADE_DATE", 3)
    if ok and d:
        out["sources"]["northbound"] = "✅ 东财"
        latest = d[0]
        out["readings"]["northbound_hold_ratio"] = latest.get("HOLD_SHARES_RATIO")
        out["readings"]["northbound_hold_shares"] = latest.get("HOLD_SHARES")
        out["readings"]["northbound_date"] = str(latest.get("TRADE_DATE", ""))[:10]
    else:
        out["sources"]["northbound"] = f"⚠️ {d}"

    # 缺口
    out["gaps"].append("主力/超大单净流入 (push2his) — 当前 IP 被限, 需用 MCP get_fund_flow")
    return out


# ============================================================================
# 维度 3: 基本面
# ============================================================================

def dim_fundamentals(code: str, market: str) -> dict:
    out = {"dimension": "fundamentals", "status": "ok", "readings": {}, "gaps": [], "sources": {}}

    # 财务指标
    ok, d = _try(em_datacenter, "RPT_LICO_FN_CPD", f'(SECURITY_CODE="{code}")', "REPORTDATE", 3)
    if ok and d:
        out["sources"]["financial_indicators"] = "✅ 东财"
        latest = d[0]
        keep = ["REPORTDATE", "TOTAL_OPERATE_INCOME", "PARENT_NETPROFIT", "WEIGHTAVG_ROE",
                "BASIC_EPS", "BPS", "TOTAL_ASSETS", "TOTAL_LIABILITIES"]
        out["readings"]["latest_report"] = {k: latest.get(k) for k in keep if k in latest}
        if len(d) >= 2:
            try:
                yoy = (float(d[0]["PARENT_NETPROFIT"]) / float(d[1]["PARENT_NETPROFIT"]) - 1) * 100
                out["readings"]["netprofit_yoy_pct"] = round(yoy, 1)
            except Exception:
                pass
    else:
        out["sources"]["financial_indicators"] = f"❌ {d}"

    # 一致预期
    ok, d = _try(em_datacenter, "RPT_WEB_RESPREDICT", f'(SECURITY_CODE="{code}")', "PUBLISH_DATE", 3)
    if ok and d:
        out["sources"]["consensus"] = "✅ 东财"
        out["readings"]["consensus"] = {k: v for k, v in d[0].items()
                                        if k in ("REPORT_DATE", "EPS1", "EPS2", "EPS3", "PE1", "PE2", "PE3")}
    else:
        out["sources"]["consensus"] = f"⚠️ {d}"

    out["gaps"].append("三大报表全文 — 需 MCP get_financial_statements / SEC EDGAR")
    out["gaps"].append("分析师报告/公允价值/护城河 — 需 Morningstar MCP")
    return out


# ============================================================================
# 维度 4: 宏观
# ============================================================================

def dim_macro(code: str, market: str) -> dict:
    out = {"dimension": "macro", "status": "ok", "readings": {}, "gaps": [], "sources": {}}
    try:
        import akshare as ak
    except ImportError:
        out["status"] = "fail"
        out["error"] = "akshare 未安装"
        return out

    # 各 series 结构不同, 需分别处理 (ascending/descending, 列名不同)
    specs = [
        # name, fn, date_col, value_col, descending(新在前)
        ("china_cpi_yoy", lambda: ak.macro_china_cpi(), "月份", "全国-同比增长", True),
        ("china_ppi_yoy", lambda: ak.macro_china_ppi(), "月份", "当月同比增长", True),
        ("china_m2_yoy", lambda: ak.macro_china_money_supply(), "月份",
         "货币和准货币(M2)-同比增长", True),
        ("china_shrzgm", lambda: ak.macro_china_shrzgm(), "月份", "社会融资规模增量", False),
        ("china_gdp_yoy", lambda: ak.macro_china_gdp_yearly(), "日期", "今值", False),
    ]
    for name, fn, dcol, vcol, desc in specs:
        ok, df = _try(fn)
        if not ok or df is None or len(df) == 0:
            out["sources"][name] = f"❌ {df}"
            continue
        try:
            d2 = df.dropna(subset=[vcol])
            if len(d2) == 0:
                out["sources"][name] = "⚠️ 全为 NaN"
                continue
            row = d2.iloc[0] if desc else d2.iloc[-1]
            out["sources"][name] = "✅ akshare"
            out["readings"][name] = {"date": str(row.get(dcol)), "value": float(row.get(vcol))}
        except Exception as e:
            out["sources"][name] = f"❌ 解析: {type(e).__name__}"

    # HYP-029 中国反向操作 5 项触发监控 (CPI≥2% / PPI转正 / M2>9% / 社融 / 工业利润)
    trig = {}
    cpi = out["readings"].get("china_cpi_yoy", {}).get("value")
    if cpi is not None:
        trig["CPI ≥ 2%"] = "✅" if cpi >= 2 else f"❌ ({cpi})"
    ppi = out["readings"].get("china_ppi_yoy", {}).get("value")
    if ppi is not None:
        trig["PPI 转正"] = "✅" if ppi > 0 else f"❌ ({ppi})"
    m2 = out["readings"].get("china_m2_yoy", {}).get("value")
    if m2 is not None:
        trig["M2 > 9%"] = "✅" if m2 > 9 else f"❌ ({m2})"
    if trig:
        out["readings"]["hyp029_trigger_status"] = trig

    out["gaps"].append("美国宏观 (CPI/Fed Funds/NFCI/PCE/收益率曲线) — 需 MCP llmquant-data_macro_*")
    out["gaps"].append("事件隐含概率 — 需 MCP llmquant-data_polymarket_*")
    return out


# ============================================================================
# 汇总
# ============================================================================

DIMENSIONS = {
    "volume": dim_volume_structure,
    "fund": dim_fund_flow,
    "fundamentals": dim_fundamentals,
    "macro": dim_macro,
}


def run(args) -> dict:
    dims = args.dimensions.split(",") if args.dimensions else list(DIMENSIONS.keys())
    results = []
    for d in dims:
        fn = DIMENSIONS.get(d)
        if not fn:
            continue
        results.append(fn(args.code, args.market))

    # 数据新鲜度检查 (宏观序列 > 90 天 = stale)
    stale_flags = []
    for dim in results:
        if dim["dimension"] != "macro":
            continue
        for k, v in dim.get("readings", {}).items():
            if not isinstance(v, dict) or "date" not in v:
                continue
            ds = str(v["date"]).replace("年", "-").replace("月份", "").replace("-", "-")
            m = None
            import re as _re
            mm = _re.match(r"(\d{4})[-]?(\d{1,2})", ds)
            if mm:
                y, mo = int(mm.group(1)), int(mm.group(2))
                age_days = (datetime.now() - datetime(y, mo, 1)).days
                if age_days > 90:
                    stale_flags.append(f"{k} 数据陈旧 ({v['date']}, {age_days} 天前)")

    payload = {
        "meta": {
            "code": args.code, "market": args.market,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "dimensions": dims,
            "stale_flags": stale_flags,
        },
        "dimensions": results,
        "cross_validation_hint": (
            "本证据层应与 trend-analysis-multi-algo 的价格算法交叉验证："
            "若 10 个价格算法共识度低（分歧），但非价格证据方向一致 → 非价格维度可能是"
            "领先信号；若两者同向且证据强 → 提高置信度；若两者矛盾 → 标注为未决。"
            "注意：价格类算法内部是同一数据的变换（伪独立），非价格维度才是真正独立证据。"
        ),
    }
    return payload


def main():
    ap = argparse.ArgumentParser(description="非价格证据采集")
    ap.add_argument("--code", default="601788")
    ap.add_argument("--market", default="sh", choices=["sh", "sz", "bj"])
    ap.add_argument("--dimensions", default=None, help="volume,fund,fundamentals,macro")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    payload = run(args)
    m = payload["meta"]
    print("=" * 66)
    print(f"非价格证据 — {m['code']} ({m['market']}) @ {m['generated_at']}")
    print("=" * 66)
    for dim in payload["dimensions"]:
        print(f"\n【{dim['dimension']}】status={dim['status']}")
        for k, v in dim.get("readings", {}).items():
            print(f"  · {k}: {v}")
        for s, st in dim.get("sources", {}).items():
            print(f"    [{st}] {s}")
        for g in dim.get("gaps", []):
            print(f"    ⚠️ 缺口: {g}")
        if dim.get("error"):
            print(f"    ❌ {dim['error']}")
    print("\n" + "-" * 66)
    print(payload["cross_validation_hint"])

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\nJSON → {args.json_out}")


if __name__ == "__main__":
    main()
