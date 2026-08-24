"""pool_topup.py — 对未达标区域循环补齐(幂等upsert), 每轮间隔120s"""
import sys, os, time, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH, DP, SIZE_THRESHOLD_NATIVE, SCREENER_TABLE
from mcp_client import MorningstarMCPClient
import s1_build_universe as s1

TARGETS = {  # region -> (country, cap)
    "UK": ("United Kingdom", 1000), "FR": ("France", 500), "CH": ("Switzerland", 500),
    "DE": ("Germany", 500), "IT": ("Italy", 500),
    "JP": ("Japan", 150), "TW": ("Taiwan", 150), "AU": ("Australia", 150), "SG": ("Singapore", 150),
}
REGION_CODE = {"United Kingdom":"UK","France":"FR","Switzerland":"CH","Germany":"DE",
               "Italy":"IT","Japan":"JP","Taiwan":"TW","Australia":"AU","Singapore":"SG"}

def counts(cur):
    cur.execute(f"SELECT region, COUNT(*) FROM {SCREENER_TABLE} GROUP BY region")
    return dict(cur.fetchall())

def main():
    con = sqlite3.connect(DB_PATH)
    client = MorningstarMCPClient()
    for attempt in range(1, 4):
        c = counts(con.cursor())
        todo = [(r, *TARGETS[r]) for r in TARGETS if c.get(r, 0) < TARGETS[r][1]]
        if not todo:
            print("ALL TARGETS MET"); return
        print(f"[attempt {attempt}] todo: {[(r,c.get(r,0),'/',cap) for r,_,cap in todo]}", flush=True)
        for region, country, cap in todo:
            rows = s1.paginate(client, "FO",
                [{"datapoint_id": DP["size_usd"], "operator": ">", "value": str(SIZE_THRESHOLD_NATIVE)},
                 {"datapoint_id": "LS017", "operator": "=", "value": country}],
                f"TOPUP/{country}", cap=cap, max_pages=cap//100+2)
            for r in rows:
                r.update(region=REGION_CODE[country], _dom=country)
            cur = con.cursor()
            # 只补缺失的mid, 不动已有行(passed语义保留)
            new = []
            exist = {x[0] for x in cur.execute(
                f"SELECT morningstar_id FROM {SCREENER_TABLE} WHERE region=?", (region,))}
            new = [r for r in rows if r.get("morningstar_id") not in exist]
            s1.write_rows(cur, new)
            con.commit()
            c2 = counts(cur)
            print(f"  {region}: +{len(new)} -> {c2.get(region)}/{cap}", flush=True)
            time.sleep(60)   # 国家间休息, 缓解限流
        time.sleep(120)

if __name__ == "__main__":
    main()
