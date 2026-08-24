"""
expand_regions.py — v1.5 区域/品种扩张编排器
会话结构（每两次拉取之间 sleep 600s，用户契约）:
  S0 pools → S1 probe(OF99A) → [600s] → S2 US-inst+UK → ingest → [600s]
  → S3 IE → ingest → [600s] → S4 EU4-Top1000 → ingest → [600s]
  → S5 APAC4-Top200 → ingest → [600s] → S6 holdings(all) → ingest → finalize
支持断点: /tmp/expand_state.json 记录已完成 session。
"""
import sys, os, json, time, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (DB_PATH, DP, DP_FUND_MASTER, BATCH_SIZE, SCREENER_TABLE,
                    dated_raw_subdir)
from mcp_client import MorningstarMCPClient
import s1_build_universe as s1
import s4_ingest as s4

STATE = '/tmp/expand_state.json'
LOG = '/tmp/expand.log'
SLEEP = 600

def log(m):
    line = f'{time.strftime("%m-%d %H:%M:%S")} {m}'
    with open(LOG, 'a') as f:
        f.write(line + '\n')
    print(line, flush=True)

def state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}

def save(st):
    json.dump(st, open(STATE, 'w'))

def get_client():
    return MorningstarMCPClient()

# ---------- Session 实现 ----------

_con = None
def CON():
    global _con
    if _con is None:
        _con = sqlite3.connect(DB_PATH)
    return _con

def s_pools(c):
    outdir = dated_raw_subdir('expansion_pools')
    s1.build_us_inst(CON(), c, outdir, top_n=20)
    s1.build_geo_multi(CON(), c, outdir,
        [("United Kingdom", "UK")], per_country_cap=1200)
    s1.build_geo_multi(CON(), c, outdir,
        [("Ireland", "IE")], per_country_cap=1200)
    s1.build_geo_multi(CON(), c, outdir,
        [("France", "FR"), ("Switzerland", "CH"), ("Germany", "DE"), ("Italy", "IT")],
        per_country_cap=500)
    s1.build_geo_multi(CON(), c, outdir,
        [("Japan", "JP"), ("Taiwan", "TW"), ("Australia", "AU"), ("Singapore", "SG")],
        per_country_cap=150)

def pool_mids(regions):
    cur = CON().cursor()
    qmarks = ",".join("?" * len(regions))
    cur.execute(f"""SELECT morningstar_id FROM {SCREENER_TABLE}
                    WHERE region IN ({qmarks})""", regions)
    return [r[0] for r in cur.fetchall()]

def probe_usd(c, mids):
    """OF99A 探针: 返回 {mid: usd_float}"""
    out = {}
    for i in range(0, len(mids), BATCH_SIZE):
        b = mids[i:i+BATCH_SIZE]
        try:
            r = c.get_data(b, [DP["size_usd"]])
            if r:
                for mid, d in r.items():
                    if isinstance(d, dict) and d.get("values"):
                        for v in d["values"]:
                            if v.get("datapointId") == DP["size_usd"]:
                                try:
                                    out[mid] = float(v["value"])
                                except (TypeError, ValueError):
                                    pass
        except Exception as e:
            log(f"  probe err@{i}: {e}")
        if (i // BATCH_SIZE + 1) % 20 == 0:
            log(f"  probe {i+len(b)}/{len(mids)}")
        time.sleep(0.2)
    return out

def select_top(region_list, cap, usd_map):
    rows = CON().execute(f"""
        SELECT morningstar_id FROM {SCREENER_TABLE}
        WHERE region IN ({','.join('?'*len(region_list))})""",
        region_list).fetchall()
    mids = [r[0] for r in rows]
    scored = sorted(((usd_map.get(m, 0), m) for m in mids), reverse=True)
    return [m for _, m in scored[:cap]]

def pull_master_and_ingest(c, region_key, fund_type, mids, outdir, tag):
    done_path = outdir / f"master_{tag}.json"
    done = json.loads(done_path.read_text()) if done_path.exists() else {}
    todo = [m for m in mids if m not in done]
    log(f"[{tag}] master pull: {len(todo)} (cached {len(done)})")
    for i in range(0, len(todo), BATCH_SIZE):
        b = todo[i:i+BATCH_SIZE]
        try:
            r = c.get_data(b, DP_FUND_MASTER)
            if r:
                got = False
                for mid, d in r.items():
                    if isinstance(d, dict) and d.get("values"):
                        done[mid] = {v["datapointId"]: v.get("value") for v in d["values"]}
                        got = True
                if not got:                      # 整批无效ID -> 记跳过标记
                    for mid in b:
                        done.setdefault(mid, None)
            else:                                # 工具级错误(isError) -> 跳过该批
                for mid in b:
                    done.setdefault(mid, None)
        except Exception as e:
            log(f"  ERR@{i}: {e}")
            if "401" in str(e):
                c = get_client()
        if (i // BATCH_SIZE + 1) % 25 == 0:
            done_path.write_text(json.dumps(done))
            log(f"  [{tag}] {i+len(b)}/{len(todo)}")
        time.sleep(0.2)
    done_path.write_text(json.dumps(done))
    flat = {m: d for m, d in done.items() if m in set(mids)}
    s4.ingest_master(CON(), flat, region_key, default_fund_type=fund_type)

def pull_holdings_ingest(c, mids, outdir, tag):
    path = outdir / f"holdings_{tag}.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    todo = [m for m in mids if m not in done]
    log(f"[{tag}] holdings: {len(todo)}")
    for i in range(0, len(todo), BATCH_SIZE):
        b = todo[i:i+BATCH_SIZE]
        try:
            r = c.get_holdings(b, num_holdings=10)
            if r and "results" in r:
                for e in r["results"]:
                    for mid, hl in e.get("holdings", {}).items():
                        done[mid] = {"as_of_date": e.get("as_of_date", ""), "holdings": hl}
        except Exception as e:
            log(f"  ERR@{i}: {e}")
            if "401" in str(e):
                c = get_client()
        if (i // BATCH_SIZE + 1) % 50 == 0:
            path.write_text(json.dumps(done))
            log(f"  [{tag}] {i+len(b)}/{len(todo)}")
        time.sleep(0.2)
    path.write_text(json.dumps(done))
    s4.ingest_holdings(CON(), done)

# ---------- 主流程 ----------
import os as _os
SESSIONS = _os.environ.get("EXPAND_SESSIONS",
    "pools,probe,uk_batch,ie_batch,eu4_batch,apac_batch,holdings").split(",")

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    st = state()
    c = get_client()
    outdir = dated_raw_subdir('expansion')

    for idx, name in enumerate(SESSIONS):
        if st.get(name):
            log(f"skip {name} (done)")
            continue
        if idx > 0:                      # 会话间强制休眠
            log(f"... sleeping {SLEEP}s before {name} ...")
            time.sleep(SLEEP)
        log(f"=== SESSION {name} start ===")

        if name == "pools":
            s_pools(c)

        elif name == "probe":
            mids_eu4 = pool_mids(["FR", "CH", "DE", "IT"])
            mids_apac = pool_mids(["JP", "TW", "AU", "SG"])
            log(f"probe targets: eu4={len(mids_eu4)} apac={len(mids_apac)}")
            usd = probe_usd(c, mids_eu4 + mids_apac)
            json.dump(usd, open(outdir / "probe_usd.json", "w"))
            st["probe_count"] = len(usd); save(st)

        elif name == "uk_batch":
            uk = select_top(["UK"], 1000, {})          # 单币种国家: 池序即规模序
            log(f"UK selected {len(uk)}")
            pull_master_and_ingest(c, "uk", "open_end", uk, outdir, "uk")
            # US 机构三件套
            inst = pool_mids(["US"])                   # CEF/CZ/SA 已在 US 区(universe 区分)
            cu = CON().cursor()
            cu.execute(f"""SELECT morningstar_id, universe FROM {SCREENER_TABLE}
                           WHERE region='US' AND universe IN ('FC','CZ','SA')""")
            ftype = {"FC": "closed_end", "CZ": "cit", "SA": "separate_account"}
            by_type = {}
            for mid, uni in cu.fetchall():
                by_type.setdefault(ftype[uni], []).append(mid)
            for ft, mids in by_type.items():
                pull_master_and_ingest(c, "us", ft, mids, outdir, f"us_{ft}")

        elif name == "ie_batch":
            ie = select_top(["IE"], 1000, {})
            log(f"IE selected {len(ie)}")
            pull_master_and_ingest(c, "ie", "open_end", ie, outdir, "ie")

        elif name == "eu4_batch":
            usd = json.load(open(outdir / "probe_usd.json"))
            top = select_top(["FR", "CH", "DE", "IT"], 1000, usd)
            log(f"EU4 selected {len(top)}")
            # 按 LS017 实际国别分桶入库(公司归属更准): 简化——统一挂 FR 公司键? 
            # 更准: 用池表 search_country 分派 region_key
            cur = CON().cursor()
            buckets = {}
            for mid in top:
                cur.execute(f"SELECT search_country FROM {SCREENER_TABLE} WHERE morningstar_id=? AND region IN ('FR','CH','DE','IT')", (mid,))
                row = cur.fetchone()
                country = (row[0] if row else "France").lower()
                key = {"france": "fr", "switzerland": "ch", "germany": "de", "italy": "it"}.get(country, "fr")
                buckets.setdefault(key, []).append(mid)
            for rk, mids in buckets.items():
                pull_master_and_ingest(c, rk, "open_end", mids, outdir, f"eu4_{rk}")

        elif name == "apac_batch":
            usd = json.load(open(outdir / "probe_usd.json"))
            top = select_top(["JP", "TW", "AU", "SG"], 200, usd)
            log(f"APAC selected {len(top)}")
            cur = CON().cursor()
            buckets = {}
            for mid in top:
                cur.execute(f"SELECT search_country FROM {SCREENER_TABLE} WHERE morningstar_id=? AND region IN ('JP','TW','AU','SG')", (mid,))
                row = cur.fetchone()
                country = (row[0] if row else "Japan").lower()
                key = {"japan": "jp", "taiwan": "tw", "australia": "au", "singapore": "sg"}.get(country, "jp")
                buckets.setdefault(key, []).append(mid)
            for rk, mids in buckets.items():
                pull_master_and_ingest(c, rk, "open_end", mids, outdir, f"apac_{rk}")

        elif name == "holdings":
            all_new = []
            for f in sorted(outdir.glob("master_*.json")):
                all_new.extend(json.load(open(f)).keys())
            all_new = list(dict.fromkeys(all_new))
            log(f"holdings target total: {len(all_new)}")
            pull_holdings_ingest(c, all_new, outdir, "expansion_all")
            # 收尾
            import s5_finalize
            con = CON()
            s5_finalize.finalize_vehicles(con)
            try:
                s5_finalize.fix_types(con)
            except AssertionError as e:
                log(f"WARN fix_types: {e}")
            s5_finalize.rebuild_views(con)
            s5_finalize.refresh_db_stats(con)
            con.commit()
            log("finalize done")

        st[name] = True
        st[f"{name}_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save(st)
        log(f"=== SESSION {name} DONE ===")

    log("🎉 ALL EXPANSION SESSIONS COMPLETE")

if __name__ == "__main__":
    main()
