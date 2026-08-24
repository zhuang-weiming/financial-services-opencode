"""
s2_pull_fund_master.py — 主数据拉取（OF99A 美元口径优先）
输入: screener 池中尚未入库/需刷新的 morningstar_id
特性: checkpoint 断点续拉、401自动重初始化、按日期目录落盘
用法: python3 s2_pull_fund_master.py --region us|eu|cn_hk [--refresh]
"""
import argparse, json, sqlite3, time
from config import (DB_PATH, DP_FUND_MASTER, BATCH_SIZE,
                    CHECKPOINT_EVERY_BATCHES, dated_raw_subdir, SCREENER_TABLE, REGION_FILTER)
from mcp_client import MorningstarMCPClient


def pending_ids(con, region, refresh):
    cur = con.cursor()
    filt = REGION_FILTER[region]
    sql = f"SELECT s.morningstar_id FROM {SCREENER_TABLE} s "
    if not refresh:
        sql += ("LEFT JOIN fund f ON f.morningstar_id=s.morningstar_id "
                f"WHERE {filt} AND f.morningstar_id IS NULL ")
    else:
        sql += f"WHERE {filt} "
    sql += "ORDER BY s.morningstar_id"
    return [r[0] for r in cur.execute(sql).fetchall()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True, choices=list(REGION_TABLE))
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()

    outdir = dated_raw_subdir(f"master_{a.region}")
    ckpt = outdir / "checkpoint.json"
    done = json.loads(ckpt.read_text()) if ckpt.exists() else {}

    con = sqlite3.connect(DB_PATH)
    ids = [m for m in pending_ids(con, a.region, a.refresh) if m not in done]
    print(f"[{a.region}] pending={len(ids)} (done={len(done)})")
    if not ids:
        return

    client = MorningstarMCPClient()
    pulled = errs = 0
    t0 = time.time()
    for i in range(0, len(ids), BATCH_SIZE):
        batch = ids[i:i + BATCH_SIZE]
        try:
            r = client.get_data(batch, DP_FUND_MASTER)
            if r:
                for mid, d in r.items():
                    if isinstance(d, dict) and d.get("values"):
                        done[mid] = {v["datapointId"]: v.get("value") for v in d["values"]}
                        pulled += 1
                    else:
                        errs += 1
        except Exception as e:
            print(f"  ERR@{i}: {e}")
            errs += len(batch)
            if "401" in str(e):
                client = MorningstarMCPClient()   # token 过期自愈
        if (i // BATCH_SIZE + 1) % CHECKPOINT_EVERY_BATCHES == 0:
            ckpt.write_text(json.dumps(done))
            el = time.time() - t0
            rate = pulled / el * 60 if el else 0
            print(f"  batch {i//BATCH_SIZE+1}: ok={pulled} err={errs} rate={rate:.0f}/min")
        time.sleep(0.2)

    ckpt.write_text(json.dumps(done))
    final = outdir / f"master_{a.region}.json"
    final.write_text(json.dumps(done, indent=1))
    print(f"DONE ok={pulled} err={errs} -> {final}")


if __name__ == "__main__":
    main()
