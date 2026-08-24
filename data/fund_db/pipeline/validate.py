"""
validate.py — DB 质量断言（只读，随时可跑）
基线依据: schema_v1.3.md §8
"""
import sqlite3, sys
from config import DB_PATH

FAIL = []
def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗ FAIL'} {name}" + (f"  [{detail}]" for _ in [0]).__next__() if detail and not cond else f"  {'✓' if cond else '✗ FAIL'} {name}")
    if not cond:
        FAIL.append(name)


def refresh_db_stats(con_cur):
    """M7: 将关键计数写入 db_stats(文档引用源)。"""
    from config import STATS_QUERIES
    for k, q in STATS_QUERIES.items():
        con_cur.execute(q)
        v = str(con_cur.fetchone()[0])
        con_cur.execute("INSERT INTO db_stats(stat_key,stat_value) VALUES (?,?) "
                        "ON CONFLICT(stat_key) DO UPDATE SET stat_value=excluded.stat_value, "
                        "updated_at=datetime('now')", (k, v))


def main():
    con = sqlite3.connect(DB_PATH)   # 可写: 需刷新 db_stats
    refresh_db_stats(con.cursor())
    con.commit()
    con.close()
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = con.cursor()
    print("=" * 64)
    print("fund_db.sqlite QA 断言")
    print("=" * 64)

    # 0 完整性
    cur.execute("PRAGMA integrity_check")
    check("integrity_check=ok", cur.fetchone()[0] == "ok")

    # 1 唯一性 (R1)
    cur.execute("""SELECT COUNT(*) FROM (SELECT morningstar_id FROM fund
                   WHERE morningstar_id IS NOT NULL GROUP BY morningstar_id HAVING COUNT(*)>1)""")
    d = cur.fetchone()[0]
    check("morningstar_id 无重复", d == 0, f"{d} dup")

    # 2 类型一致性 (R5)
    cur.execute("""SELECT f.fund_type t, s.universe u FROM fund f
                   JOIN fund_screener_pool s ON f.morningstar_id=s.morningstar_id
                   WHERE s.region='US'""")
    OK = {'FE':'ETF','FO':'open_end','FC':'closed_end','CZ':'cit','SA':'separate_account'}
    bad = sum(1 for t, u in cur.fetchall() if OK.get(u) != t)
    check("fund_type×universe 一致", bad == 0, f"{bad}")

    # 3 规模口径 (R2): size_usd 必有币种标签；本币规模列与USD列不得混用
    cur.execute("SELECT COUNT(*) FROM fund WHERE size_usd IS NOT NULL AND size_currency IS NULL")
    n = cur.fetchone()[0]
    check("size_usd 行均有 size_currency", n == 0, f"{n} missing ccy")

    # 4 规模合理性: 同一 vehicle 簇内 size_usd 极差 <1%（真不变量）
    cur.execute("""
        SELECT vehicle_mid, MIN(size_usd), MAX(size_usd), COUNT(*)
        FROM fund
        WHERE size_usd IS NOT NULL AND morningstar_id IN (
            SELECT listing_mid FROM fund_listing_map)
        GROUP BY vehicle_mid HAVING COUNT(size_usd)>1""")
    worst, worst_n = 0.0, ""
    for vmid, lo, hi, c in cur.fetchall():
        if lo and hi:
            span = (hi - lo) / max(hi, 1) * 100
            if span > worst:
                worst, worst_n = span, f"{vmid}({c})"
    from config import QA_MAX_SPAN_PCT_IN_LISTING_GROUP as LIM
    check(f"同名组 size_usd 极差<{LIM}%", worst <= LIM, f"worst={worst:.2f}% {worst_n}")

    # 5 明星基金锚点抽查
    anchors = {"Invesco QQQ Trust": (400e9, 600e9),
               "iShares Core S&P 500 ETF": (700e9, 1000e9),
               "Vanguard Total Stock Market ETF": (1.8e12, 2.8e12)}
    for nm, (lo, hi) in anchors.items():
        cur.execute("SELECT size_usd FROM fund WHERE fund_name=? AND size_usd IS NOT NULL LIMIT 1", (nm,))
        r = cur.fetchone()
        ok = r and lo <= r[0] <= hi
        check(f"锚点[{nm}] size∈[{lo/1e9:.0f}B,{hi/1e9:.0f}B]", bool(ok),
              f"{(r[0]/1e9 if r else 'NULL')}B")

    # 6 持仓审计 (R7)
    cur.execute("""SELECT COUNT(*) FROM fund_holdings_snapshot
                   WHERE COALESCE(weight_quarantine,0)=0
                     AND COALESCE(is_notional,0)=0
                     AND ABS(weight_pct)>100""")
    q = cur.fetchone()[0]
    check("clean 持仓权重⊆[-100,100]", q == 0, f"{q} 违规")

    # 7 launch_date 覆盖
    cur.execute("""SELECT SUM(CASE WHEN f.launch_date IS NULL THEN 1 ELSE 0 END) nl, COUNT(*) n
                   FROM fund f JOIN fund_screener_pool s ON f.morningstar_id=s.morningstar_id
                   WHERE s.region IN ('CN','HK')""")
    nl, n = cur.fetchone()
    check("CN/HK launch_date 缺失<2%", (nl or 0)/max(n,1) < 0.02, f"{nl}/{n}")

    # 8 CN/HK 双腿契约 (修复#4)
    cur.execute("SELECT COUNT(*) FROM fund_screener_pool WHERE region='HK'")
    hk_n = cur.fetchone()[0]
    check("池含香港腿(region=HK)", hk_n > 0, str(hk_n))

    # 9 护栏视图存在且非空
    for v, minrows in [("v_fund_screen", 15000), ("v_fund_sharpe_clean", 15000),
                       ("v_holdings_latest", 15000)]:
        try:
            col = "COUNT(DISTINCT fund_id)" if v == "v_holdings_latest" else "COUNT(*)"
            cur.execute(f"SELECT {col} FROM {v}")
            n = cur.fetchone()[0]
            check(f"视图 {v}>={minrows}", n >= minrows, str(n))
        except sqlite3.Error as e:
            check(f"视图 {v}", False, str(e))

    con.close()
    print("=" * 64)
    if FAIL:
        print(f"❌ {len(FAIL)} 项未通过: {FAIL}")
        sys.exit(1)
    print("✅ 全部断言通过")


if __name__ == "__main__":
    main()
