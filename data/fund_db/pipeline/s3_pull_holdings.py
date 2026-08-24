"""
s3_pull_holdings.py — Top-10 持仓拉取
特性: 10 ids/批(工具上限)、checkpoint、is_notional/quarantine 由 s4 入库时计算
用法: python3 s3_pull_holdings.py --region us|eu|cn_hk [--refresh]
"""
import argparse, json, sqlite3, time
from config import (DB_PATH, BATCH_SIZE, TOP_N_HOLDINGS,
                    CHECKPOINT_EVERY_BATCHES, dated_raw_subdir, SCREENER_TABLE, REGION_FILTER)
from mcp_client import MorningstarMCPClient


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True, choices=list(REGION_TABLE))
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()

    outdir = dated_raw_subdir(f"holdings_{a.region}")
    ckpt = outdir / "checkpoint.json"
    done = json.loads(ckpt.read_text()) if ckpt.exists() else {}

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    filt = REGION_FILTER[a.region]
    sql = f"SELECT DISTINCT s.morningstar_id FROM {SCREENER_TABLE} s "
    if not a.refresh:
        sql += ("JOIN fund f ON f.morningstar_id=s.morningstar_id "
                "LEFT JOIN fund_holdings_snapshot h ON h.fund_id=f.fund_id ")
        sql += (f"WHERE {filt} AND f.morningstar_id IS NOT NULL "
                "GROUP BY s.morningstar_id HAVING COUNT(h.holding_id)=0")
    else:
        sql += f"WHERE {filt}"
    sql += " ORDER BY s.morningstar_id"
    ids = [r[0] for r in cur.execute(sql).fetchall() if r[0] not in done]
    con.close()
    print(f"[{a.region}] holdings pending={len(ids)}")
    if not ids:
        return

    client = MorningstarMCPClient()
    n = errs = 0
    for i in range(0, len(ids), 10):     # 工具硬上限: ≤10 investment_ids/次
        batch = ids[i:i + 10]
        try:
            r = client.get_holdings(batch, num_holdings=TOP_N_HOLDINGS)
            if r and "results" in r:
                for entry in r["results"]:
                    as_of = entry.get("as_of_date", "")
                    for mid, hl in entry.get("holdings", {}).items():
                        done[mid] = {"as_of_date": as_of, "holdings": hl}
                        n += 1
        except Exception as e:
            print(f"  ERR@{i}: {e}")
            errs += len(batch)
            if "401" in str(e):
                client = MorningstarMCPClient()
        if (i // 10 + 1) % CHECKPOINT_EVERY_BATCHES == 0:
            ckpt.write_text(json.dumps(done))
            print(f"  batch {i//10+1}: funds={n} err={errs}")
        time.sleep(0.2)

    ckpt.write_text(json.dumps(done))
    final = outdir / f"holdings_{a.region}.json"
    final.write_text(json.dumps(done, indent=1))
    print(f"DONE funds={n} -> {final}")


if __name__ == "__main__":
    main()
