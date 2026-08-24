"""
s1_build_universe.py — 构建/刷新统一 screener 候选池 fund_screener_pool
v1.4.2: 三张区域表合并; region ∈ US|EU|CN|HK; passed_filter=0 即待拉取工作集
反污染要点:
  * US: FE>FO>FC 优先去重（同 mid 多 universe 只留最高优先）
  * CN/HK: 双腿必须都跑完（assert 契约, 历史 bug #4）
用法: python3 s1_build_universe.py --regions us,eu,cnhk
"""
import argparse, json, sqlite3, time
from config import (DB_PATH, DP, EU_DOMICILES, CNHK_COUNTRIES,
                    SIZE_THRESHOLD_NATIVE, SCREENER_TABLE, dated_raw_subdir)
from mcp_client import MorningstarMCPClient

COLS = ("region, morningstar_id, universe, fund_name, ticker, morningstar_category,"
        " net_asset_value, last_price, exchange, medalist_rating,"
        " fund_size_native, fund_size_usd, size_currency, currency,"
        " search_country, passed_filter, fetched_at")


def paginate(client, universe, criteria, tag, cap=1500, max_pages=25):
    out, token = [], ""
    for page_i in range(max_pages):
        args = {"universe": universe, "screener_criteria": criteria, "page_size": 100}
        if token:
            args["pagination_token"] = token
            args["pagination_action"] = "next"
        r = client._call_tool("morningstar-screener-tool", args)
        if not r or not r.get("results"):
            break
        out.extend(r["results"])
        print(f"    [{tag}] page{page_i+1}: +{len(r['results'])} (total {len(out)})", flush=True)
        token = r.get("pagination_token_next", "")
        if not token or len(out) >= cap:
            break
        time.sleep(0.3)
    print(f"  [{tag}] collected {len(out)}")
    return out


def write_rows(cur, rows):
    """rows: list of dict 含 region/_uni/_dom + key_datapoints"""
    n = 0
    for r in rows:
        mid = r.get("morningstar_id")
        if not mid:
            continue
        k = r.get("key_datapoints", {})
        cur.execute(f"""
            INSERT INTO {SCREENER_TABLE} ({COLS})
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
            ON CONFLICT(region, morningstar_id) DO UPDATE SET
                universe=excluded.universe, fund_name=excluded.fund_name,
                ticker=excluded.ticker, morningstar_category=excluded.morningstar_category,
                net_asset_value=excluded.net_asset_value, last_price=excluded.last_price,
                exchange=excluded.exchange, medalist_rating=excluded.medalist_rating,
                fund_size_native=excluded.fund_size_native, fund_size_usd=excluded.fund_size_usd,
                search_country=excluded.search_country""",
            (r["region"], mid, r.get("_uni"), r.get("name", ""), k.get("Ticker", ""),
             k.get("Morningstar Category", ""), k.get("Net Asset Value"),
             k.get("Last Price"), k.get("Exchange", ""),
             k.get("Morningstar Medalist Rating", ""),
             None, None, None, None,
             r.get("_dom"), 0))
        n += 1
    return n


def build_us(con, client, outdir):
    cur = con.cursor()
    prio = {"FE": 0, "FO": 1, "FC": 2}
    seen = {}
    for uni in ["FE", "FO", "FC"]:
        rows = paginate(client, uni,
                        [{"datapoint_id": DP["size_usd"], "operator": ">", "value": "100000000"},
                         {"datapoint_id": "LS017", "operator": "=", "value": "United States"}],
                        f"US/{uni}")
        for r in rows:
            m = r.get("morningstar_id")
            if m and (m not in seen or prio[uni] < seen[m]["_p"]):
                r["_uni"], r["_p"], r["region"], r["_dom"] = uni, prio[uni], "US", "United States"
                seen[m] = r
    dedup = list(seen.values())
    cur.execute(f"DELETE FROM {SCREENER_TABLE} WHERE region='US'")
    # 保留既有 pending/入库状态: 已存在行的 passed_filter 不被重置为0的覆盖问题
    cur.execute(f"""UPDATE {SCREENER_TABLE} SET passed_filter=
        CASE WHEN EXISTS (SELECT 1 FROM fund f WHERE f.morningstar_id={SCREENER_TABLE}.morningstar_id)
             THEN 1 ELSE 0 END WHERE region='US'""")
    n = write_rows(cur, dedup)
    con.commit()
    print(f"US pool: {n} unique mids")
    (outdir / "us_screener.json").write_text(json.dumps(dedup, indent=1))


def build_eu(con, client, outdir):
    cur = con.cursor()
    all_rows = []
    for dom in EU_DOMICILES:
        rows = paginate(client, "FO",
                        [{"datapoint_id": "LS017", "operator": "=", "value": dom},
                         {"datapoint_id": DP["size_native"], "operator": ">",
                          "value": str(SIZE_THRESHOLD_NATIVE)}],
                        f"EU/{dom}", cap=1200)
        for r in rows:
            r.update(region="EU", _dom=dom)
        all_rows.extend(rows)
    all_rows.sort(key=lambda x: float(x.get("key_datapoints", {}).get("Last Price") or 0),
                  reverse=True)
    all_rows = all_rows[:1000]
    cur.execute(f"DELETE FROM {SCREENER_TABLE} WHERE region='EU'")
    write_rows(cur, all_rows)
    _restate_passed(cur, "EU")
    con.commit()
    print(f"EU pool: {len(all_rows)}")
    (outdir / "eu_screener.json").write_text(json.dumps(all_rows, indent=1))


def build_cnhk(con, client, outdir):
    """修复#4契约: China 与 Hong Kong 两腿都必须执行"""
    cur = con.cursor()
    per_leg_cap, final = 1300, []
    for country in CNHK_COUNTRIES:
        rows = paginate(client, "FO",
                        [{"datapoint_id": "LS017", "operator": "=", "value": country},
                         {"datapoint_id": DP["size_native"], "operator": ">",
                          "value": str(SIZE_THRESHOLD_NATIVE)}],
                        f"CNHK/{country}", cap=per_leg_cap)
        rows.sort(key=lambda x: float(x.get("key_datapoints", {}).get("Last Price") or 0),
                  reverse=True)
        rows = rows[:per_leg_cap]
        for r in rows:
            r.update(region=("HK" if country == "Hong Kong" else "CN"), _dom=country)
        final.extend(rows)
    cur.execute(f"DELETE FROM {SCREENER_TABLE} WHERE region IN ('CN','HK')")
    write_rows(cur, final)
    _restate_passed(cur, "CN"); _restate_passed(cur, "HK")
    con.commit()
    from collections import Counter
    c = Counter(r["region"] for r in final)
    print(f"CN/HK pool: {dict(c)}")
    assert c.get("HK", 0) > 0, "香港腿为空 —— 违反双腿契约!"
    (outdir / "cnhk_screener.json").write_text(json.dumps(final, indent=1))


def _restate_passed(cur, region):
    """重建池后按入库存在性恢复 passed_filter（1=已入库, 0=pending）"""
    cur.execute(f"""UPDATE {SCREENER_TABLE} SET passed_filter=
        CASE WHEN EXISTS (SELECT 1 FROM fund f
                          WHERE f.morningstar_id={SCREENER_TABLE}.morningstar_id)
             THEN 1 ELSE 0 END WHERE region=?""", (region,))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", default="us,eu,cnhk")
    a = ap.parse_args()
    outdir = dated_raw_subdir("screener")
    con = sqlite3.connect(DB_PATH)
    client = MorningstarMCPClient()
    for rg in a.regions.split(","):
        rg = rg.strip()
        if rg == "us":   build_us(con, client, outdir)
        elif rg == "eu": build_eu(con, client, outdir)
        elif rg == "cnhk": build_cnhk(con, client, outdir)
    con.close()


# ═══════════════ v1.5 区域扩张 ═══════════════

def build_us_inst(con, client, outdir, top_n=20):
    """US 机构三件套: CEF(FC)/CIT(CZ)/SA 各 Top-N。
    关键优化: FC/CZ/SA universe 服务端查询极慢(~16s/页), Top-N<=100 时只取单页。"""
    cur = con.cursor()
    total = {}
    for uni, region in [("FC", "US"), ("CZ", "US"), ("SA", "US")]:
        t0 = time.time()
        r = client._call_tool("morningstar-screener-tool", {
            "universe": uni,
            "screener_criteria": [
                {"datapoint_id": DP["size_usd"], "operator": ">", "value": "100000000"},
                {"datapoint_id": "LS017", "operator": "=", "value": "United States"}],
            "page_size": min(top_n, 100)})
        rows = (r or {}).get("results", [])[:top_n]
        print(f"    [US-INST/{uni}] {len(rows)} funds in {time.time()-t0:.0f}s", flush=True)
        for rr in rows:
            rr.update(region=region, _uni=uni, _dom="United States")
        write_rows(cur, rows)
        total[uni] = len(rows)
    con.commit()
    print(f"US institutional pools: {total}")
    (outdir / "us_inst_screener.json").write_text(json.dumps(
        {"CEF": total.get("FC"), "CIT": total.get("CZ"), "SA": total.get("SA")}, indent=1))


def build_geo_multi(con, client, outdir, specs, per_country_cap):
    """多国收集(不做跨币种排序——由探针阶段完成): specs=[(country, region_code)]"""
    cur = con.cursor()
    all_rows = []
    for country, region in specs:
        rows = paginate(client, "FO",
                        [{"datapoint_id": "LS017", "operator": "=", "value": country},
                         {"datapoint_id": DP["size_usd"], "operator": ">", "value": str(SIZE_THRESHOLD_NATIVE)}],
                        f"GEO/{country}", cap=per_country_cap)
        for r in rows:
            r.update(region=region, _dom=country)
        all_rows.extend(rows)
    write_rows(cur, all_rows)
    con.commit()
    from collections import Counter
    c = Counter(r["region"] for r in all_rows)
    print(f"geo pool collected: {dict(c)}")
    return all_rows
