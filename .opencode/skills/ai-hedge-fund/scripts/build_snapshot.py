#!/usr/bin/env python3
"""
build_snapshot.py — 本地数据适配器 v3 (严格对齐 ai-hedge-fund 上游 schema)

⚠️ 设计原则 (v3): **绝不臆造指标**。输出的快照字段与派生聚合公式
   逐字对齐上游 `hedge_fund/features/snapshot.py`，persona 看到的数据
   与原生 aihf 完全一致。

上游 schema (PeriodFundamentals, 14 字段):
    report_period, filing_date, market_cap, price_to_earnings_ratio,
    return_on_equity, gross_margin, operating_margin, net_margin,
    debt_to_equity, current_ratio, revenue_growth, earnings_per_share,
    book_value_per_share, free_cash_flow_per_share

上游派生聚合 (FundamentalsSnapshot, 6 个):
    roe_avg, net_margin_avg, gross_margin_trend, bvps_cagr,
    debt_to_equity_latest, market_cap_latest

上游公式 (逐字复制):
    _avg(values)   = round(sum(xs)/len(xs), 4)              # 全部非空值
    _trend(values) = round(xs[0] - xs[-1], 4)               # newest - oldest
    _cagr(values)  = round((xs[0]/xs[-1])**(1/years)-1, 4)  # years=(len-1)/4
    _fmt(v)        = B/M 后缀 + 2 位小数 / "-" for None

数据源: 东财 RPT_F10_FINANCE_MAINFINADATA (165 字段) + 腾讯历史价
口径: TTM (滚动 12 月)，流量类 TTM 化，比率类由 TTM 流量重算

用法:
    python3 build_snapshot.py --code 601788 --market sh
    python3 build_snapshot.py --code 601788 --market sh --render
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime

import requests

H = {"User-Agent": "Mozilla/5.0"}
EM_DC = "https://datacenter-web.eastmoney.com/api/data/v1/get"
TX_KLINE = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
MIN_PERIODS = 4
PERIODS_LIMIT = 20   # 上游 build_snapshot(periods=20)

# 东财字段 → 上游 FinancialMetrics 字段名 (仅映射上游用到的)
SRC = {
    "earnings_per_share": "EPSJB",
    "book_value_per_share": "BPS",
    "free_cash_flow_per_share": "MGJYXJJE",   # 每股经营现金流 (上游为 FCF/share)
    "return_on_equity": "ROEJQ",              # 占位, 后面 TTM 重算
    "gross_margin": "XSMLL",
    "operating_margin": "OPERATE_PROFIT_PK",  # 占位, 用 /收入 算
    "net_margin": "XSJLL",                    # 占位, TTM 重算
    "debt_to_equity": "CQBL",                 # 产权比率
    "current_ratio": "LD",
    # 流量类 (用于 TTM 计算)
    "revenue": "TOTALOPERATEREVE",
    "net_income": "PARENTNETPROFIT",
    "operating_profit": "OPERATE_PROFIT_PK",
    "total_equity": "TOTAL_EQUITY_PK",
    "total_assets": "TOTAL_ASSETS_PK",
    "total_shares": "TOTAL_SHARE",
}


# ── 上游公式 (逐字复制) ──────────────────────────────────────────────
def _avg(values):
    xs = [v for v in values if v is not None]
    return round(sum(xs) / len(xs), 4) if xs else None


def _trend(values):
    """Latest minus oldest (values arrive newest first)."""
    xs = [v for v in values if v is not None]
    return round(xs[0] - xs[-1], 4) if len(xs) >= 2 else None


def _cagr(values):
    """Annualized growth from oldest to latest (ttm rows are quarter-spaced)."""
    xs = [v for v in values if v is not None]
    if len(xs) < 2 or xs[-1] is None or xs[-1] <= 0 or xs[0] <= 0:
        return None
    years = (len(xs) - 1) / 4
    if years <= 0:
        return None
    return round((xs[0] / xs[-1]) ** (1 / years) - 1, 4)


def _fmt(v):
    if v is None:
        return "-"
    if abs(v) >= 1e9:
        return f"{v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"{v / 1e6:.1f}M"
    return f"{v:.2f}"


# ── 数据获取 ────────────────────────────────────────────────────────
def em_datacenter(filt: str, size: int = 24) -> list:
    r = requests.get(EM_DC, params={
        "reportName": "RPT_F10_FINANCE_MAINFINADATA", "columns": "ALL",
        "filter": filt, "pageNumber": "1", "pageSize": str(size),
        "sortColumns": "REPORT_DATE", "sortTypes": "-1"}, timeout=25, headers=H)
    d = r.json()
    if d.get("result") and d["result"].get("data"):
        return d["result"]["data"]
    raise RuntimeError(d.get("message", "no data"))


SINA_KLINE = ("https://money.finance.sina.com.cn/quotes_service/api/"
               "json_v2.php/CN_MarketData.getKLineData")


def price_history(code: str, market: str) -> dict:
    """历史日线收盘价 → {date_str: close}。新浪(2000根,2018+) → 腾讯(640根,2024+) 回退。"""
    import json as _json
    # 新浪: 2000 根, 2018+
    try:
        r = requests.get(SINA_KLINE, params={
            "symbol": f"{market}{code}", "scale": "240", "ma": "no", "datalen": "2000"},
            timeout=30, headers=H)
        d = _json.loads(r.text)
        if isinstance(d, list) and d:
            return {x["day"]: float(x["close"]) for x in d}
    except Exception:
        pass
    # 回退: 腾讯 640 根
    try:
        sym = f"{market}{code}"
        r = requests.get(TX_KLINE, params={
            "param": f"{sym},day,2024-01-01,2026-12-31,640,qfq"}, timeout=30, headers=H)
        d = r.json()["data"][sym]
        key = "qfqday" if "qfqday" in d else "day"
        return {x[0]: float(x[2]) for x in d[key]}
    except Exception:
        return {}


def price_at(prices: dict, date_str: str) -> float | None:
    """取 <= date_str 的最近收盘价。"""
    if not prices:
        return None
    keys = sorted(prices.keys())
    prev = None
    for k in keys:
        if k <= date_str:
            prev = k
        else:
            break
    return prices.get(prev) if prev else None


def _n(v):
    try:
        return float(v) if v not in (None, "", "-") else None
    except (ValueError, TypeError):
        return None


# ── TTM 构建 ────────────────────────────────────────────────────────
def build_ttm_rows(rows: list[dict]) -> list[dict]:
    """把累计口径转成 TTM（滚动 12 月）。返回 list[dict] (新→旧)。"""
    by_date = {str(r["REPORT_DATE"])[:10]: r for r in rows if r.get("REPORT_DATE")}
    dates = sorted(by_date.keys(), reverse=True)
    out = []
    for d in dates:
        cur = by_date[d]
        year, mmdd = int(d[:4]), d[5:]
        is_annual = mmdd == "12-31"
        fy_key, prior_key = f"{year - 1}-12-31", f"{year - 1}-{mmdd}"

        def flow(field):
            """流量类 TTM = FY + 当期累计 − 上年同期累计"""
            if is_annual:
                return _n(cur.get(SRC[field]))
            if fy_key in by_date and prior_key in by_date:
                a = _n(by_date[fy_key].get(SRC[field]))
                b = _n(cur.get(SRC[field]))
                c = _n(by_date[prior_key].get(SRC[field]))
                if None not in (a, b, c):
                    return a + b - c
            return None

        rev = flow("revenue")
        ni = flow("net_income")
        op = flow("operating_profit")

        # 平均权益/资产 (TTM 期初=上年同期, 期末=当期)
        if (not is_annual) and prior_key in by_date:
            eq_b, eq_e = _n(by_date[prior_key].get("TOTAL_EQUITY_PK")), _n(cur.get("TOTAL_EQUITY_PK"))
            ta_b, ta_e = _n(by_date[prior_key].get("TOTAL_ASSETS_PK")), _n(cur.get("TOTAL_ASSETS_PK"))
        else:
            eq_b = eq_e = _n(cur.get("TOTAL_EQUITY_PK"))
            ta_b = ta_e = _n(cur.get("TOTAL_ASSETS_PK"))
        avg_eq = (eq_b + eq_e) / 2 if (eq_b and eq_e) else eq_e
        avg_ta = (ta_b + ta_e) / 2 if (ta_b and ta_e) else ta_e

        # TTM 重算比率
        roe = round(ni / avg_eq * 100, 4) if (ni and avg_eq) else None
        roa = round(ni / avg_ta * 100, 4) if (ni and avg_ta) else None
        net_m = round(ni / rev * 100, 4) if (ni and rev) else None
        op_m = round(op / rev * 100, 4) if (op and rev) else None

        # TTM 营收增速 = TTM营收(当期) / TTM营收(一年前) - 1
        rev_growth = None
        if rev is not None:
            # 一年前的 TTM 营收 (用去年同期为期末的 TTM)
            if prior_key in by_date:
                pk = prior_key
                pk_year = int(pk[:4])
                pk_mmdd = pk[5:]
                pk_fy, pk_prior = f"{pk_year-1}-12-31", f"{pk_year-1}-{pk_mmdd}"
                if pk_mmdd == "12-31":
                    rev_1y = _n(by_date[pk].get(SRC["revenue"]))
                elif pk_fy in by_date and pk_prior in by_date:
                    a = _n(by_date[pk_fy].get(SRC["revenue"]))
                    b = _n(by_date[pk].get(SRC["revenue"]))
                    c = _n(by_date[pk_prior].get(SRC["revenue"]))
                    rev_1y = (a + b - c) if None not in (a, b, c) else None
                else:
                    rev_1y = None
                if rev_1y and rev_1y != 0:
                    rev_growth = round((rev / rev_1y - 1) * 100, 4)

        out.append({
            "report_period": d,
            "filing_date": str(cur.get("NOTICE_DATE", ""))[:10] or None,
            "ttm": {
                "return_on_equity": roe,
                "net_margin": net_m,
                "operating_margin": op_m,
                "revenue_growth": rev_growth,
                "earnings_per_share": flow("earnings_per_share"),
                "book_value_per_share": _n(cur.get(SRC["book_value_per_share"])),  # 存量, 时点值
                "free_cash_flow_per_share": flow("free_cash_flow_per_share"),
                "gross_margin": _n(cur.get(SRC["gross_margin"])),
                "debt_to_equity": _n(cur.get(SRC["debt_to_equity"])),
                "current_ratio": _n(cur.get(SRC["current_ratio"])),
                "total_shares": _n(cur.get("TOTAL_SHARE")),
            },
        })
    return out


# ── 构建上游兼容快照 ────────────────────────────────────────────────
def build(code: str, market: str) -> dict:
    rows = em_datacenter(f'(SECUCODE="{code}.{market.upper()}")', 24)
    if not rows:
        raise RuntimeError("无财务数据")
    ttm_rows = build_ttm_rows(rows)
    prices = price_history(code, market)

    periods = []
    for p in ttm_rows[:PERIODS_LIMIT]:
        d = p["report_period"]
        px = price_at(prices, d)
        t = p["ttm"]
        shares = t.get("total_shares")
        mc = (shares * px) if (shares and px) else None
        eps = t.get("earnings_per_share")
        pe = round(px / eps, 4) if (px and eps and eps > 0) else None
        periods.append({
            "report_period": d,
            "filing_date": p["filing_date"],
            "market_cap": mc,
            "price_to_earnings_ratio": pe,
            "return_on_equity": t["return_on_equity"],
            "gross_margin": t["gross_margin"],
            "operating_margin": t["operating_margin"],
            "net_margin": t["net_margin"],
            "debt_to_equity": t["debt_to_equity"],
            "current_ratio": t["current_ratio"],
            "revenue_growth": t["revenue_growth"],
            "earnings_per_share": eps,
            "book_value_per_share": t["book_value_per_share"],
            "free_cash_flow_per_share": t["free_cash_flow_per_share"],
        })

    # 上游派生聚合 (逐字对齐公式, 用全部 periods)
    return {
        "ticker": f"{code}.{market.upper()}",
        "as_of": datetime.today().strftime("%Y-%m-%d"),
        "sector": rows[0].get("ORG_TYPE"),
        "industry": rows[0].get("ORG_TYPE"),
        "periods": periods,
        "roe_avg": _avg([p["return_on_equity"] for p in periods]),
        "net_margin_avg": _avg([p["net_margin"] for p in periods]),
        "gross_margin_trend": _trend([p["gross_margin"] for p in periods]),
        "bvps_cagr": _cagr([p["book_value_per_share"] for p in periods]),
        "debt_to_equity_latest": periods[0]["debt_to_equity"] if periods else None,
        "market_cap_latest": periods[0]["market_cap"] if periods else None,
    }


# ── 上游 render() (逐字对齐) ────────────────────────────────────────
def render(snap: dict) -> str:
    lines = [
        f"Company: {snap['ticker']}"
        + (f"  |  Sector: {snap['sector']}" if snap.get("sector") else "")
        + (f"  |  Industry: {snap['industry']}" if snap.get("industry") else ""),
        "All figures below were publicly filed by their filing dates. "
        "Treat the most recent filing shown as the present.",
        "",
        "Summary:",
        f"  Market cap (latest filed): {_fmt(snap.get('market_cap_latest'))}",
        f"  ROE avg: {_fmt(snap.get('roe_avg'))}  |  Net margin avg: {_fmt(snap.get('net_margin_avg'))}",
        f"  Gross margin trend (latest-oldest): {_fmt(snap.get('gross_margin_trend'))}",
        f"  Book value/share CAGR: {_fmt(snap.get('bvps_cagr'))}",
        f"  Debt/equity (latest): {_fmt(snap.get('debt_to_equity_latest'))}",
        "",
        "History (trailing-twelve-month periods, newest first):",
        "period | filed | mktcap | P/E | ROE | gross_m | op_m | net_m | D/E "
        "| curr | rev_gr | EPS | BVPS | FCF/sh",
    ]
    for p in snap["periods"]:
        lines.append(
            f"{p['report_period']} | {p['filing_date'] or '?'} | {_fmt(p['market_cap'])} "
            f"| {_fmt(p['price_to_earnings_ratio'])} | {_fmt(p['return_on_equity'])} "
            f"| {_fmt(p['gross_margin'])} | {_fmt(p['operating_margin'])} "
            f"| {_fmt(p['net_margin'])} | {_fmt(p['debt_to_equity'])} "
            f"| {_fmt(p['current_ratio'])} | {_fmt(p['revenue_growth'])} "
            f"| {_fmt(p['earnings_per_share'])} | {_fmt(p['book_value_per_share'])} "
            f"| {_fmt(p['free_cash_flow_per_share'])}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="构建 ai-hedge-fund FundamentalsSnapshot (v3 严格对齐上游)")
    ap.add_argument("--code", default="601788")
    ap.add_argument("--market", default="sh", choices=["sh", "sz", "bj"])
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    snap = build(args.code, args.market)
    if len(snap["periods"]) < MIN_PERIODS:
        print(f"⚠️ InsufficientData: 仅 {len(snap['periods'])} 期 (需 {MIN_PERIODS})", file=sys.stderr)

    print(render(snap) if args.render else json.dumps(snap, ensure_ascii=False, indent=2))
    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)
        print(f"\nJSON → {args.json_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
