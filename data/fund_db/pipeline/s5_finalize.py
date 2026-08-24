"""
s5_finalize.py — 入库后处理（每次入库后必跑）
  F1 载体归并: 同名组内按 前缀优先级(VEHICLE_PREFIX_PRIORITY) → max(size_usd) 选 canonical
              写 fund.vehicle_mid + fund_listing_map（历史#2）
  F2 类型一致性: 以 screener universe 权威重定 fund_type；清理源表跨universe双标签（历史#7）
  F3 视图重建: v_fund_screen / v_holdings_latest / v_fund_sharpe_clean
"""
import sqlite3
from collections import defaultdict, Counter
from config import (DB_PATH, VEHICLE_PREFIX_PRIORITY, LISTING_PREFIX,
                    QA_SHARPE_CLEAN_BOUND, SIZE_CLUSTER_REL, STATS_QUERIES)

MM_CATEGORIES = ["Money Market-Taxable", "Prime Money Market"]   # US口径; CN货基由Sharpe护栏兜底


def _prio(mid: str) -> int:
    for i, p in enumerate(VEHICLE_PREFIX_PRIORITY):
        if str(mid).startswith(p):
            return i
    return 99 if not str(mid).startswith(LISTING_PREFIX) else 999




def _size_cluster(members):
    """名称组内按 size_usd 中位数近似度二次聚类（区分同名不同基金, 如 ESGU vs USXF）"""
    import statistics
    sizes = [sz for _, sz in members if sz]
    med = statistics.median(sizes) if sizes else None
    clusters = []
    for mid, sz in members:
        placed = False
        if med:
            for cl in clusters:
                ref = statistics.median([x[1] for x in cl if x[1]]) or med
                if sz and ref and abs(sz - ref) <= SIZE_CLUSTER_REL * max(ref, sz):
                    cl.append((mid, sz)); placed = True; break
        if not placed:
            clusters.append([(mid, sz)])
    return clusters


def finalize_vehicles(con):
    cur = con.cursor()
    cur.execute("""SELECT fund_name, morningstar_id, size_usd FROM fund
                   WHERE fund_name IN (SELECT fund_name FROM fund GROUP BY fund_name HAVING COUNT(*)>1)""")
    groups = defaultdict(list)
    for n, m, s in cur.fetchall():
        groups[n].append((m, s))
    n = n_split = 0
    for name, members in groups.items():
        for cluster in (_size_cluster(members) if len(members) > 1 else [members]):
            def key(t):
                mid, sz = t
                p = _prio(mid)
                return (p, mid) if p < 99 else (99, -(sz or 0), mid)
            cluster.sort(key=key)
            canon = cluster[0][0]
            if len(cluster) < len(members):
                n_split += 1
            for mid, _ in cluster:
                conf = "high" if len(cluster) > 1 else "self"
                method = "name+size_cluster" if len(members) > 1 else "self"
                cur.execute("UPDATE fund SET vehicle_mid=? WHERE morningstar_id=?", (canon, mid))
                cur.execute("""INSERT OR REPLACE INTO fund_listing_map
                    (listing_mid, vehicle_mid, match_method, confidence)
                    VALUES (?, ?, ?, ?)""", (mid, canon, method, conf))
                n += 1
    con.commit()
    print(f"[F1] groups={len(groups)} rows_mapped={n} 同名拆分={n_split}")


def fix_types(con):
    cur = con.cursor()
    # R5: universe 权威（单universe行）
    cur.execute("""UPDATE fund SET fund_type='ETF' WHERE fund_type!='ETF'
        AND morningstar_id NOT IN (SELECT morningstar_id FROM fund_screener_pool
                                   WHERE region='US' GROUP BY morningstar_id HAVING COUNT(DISTINCT universe)>1)
        AND morningstar_id IN (SELECT morningstar_id FROM fund_screener_pool WHERE region='US' AND universe='FE')""")
    cur.execute("""UPDATE fund SET fund_type='open_end' WHERE fund_type!='open_end'
        AND morningstar_id NOT IN (SELECT morningstar_id FROM fund_screener_pool
                                   WHERE region='US' GROUP BY morningstar_id HAVING COUNT(DISTINCT universe)>1)
        AND morningstar_id IN (SELECT morningstar_id FROM fund_screener_pool WHERE region='US' AND universe='FO')""")
    cur.execute("""UPDATE fund SET fund_type='closed_end' WHERE fund_type!='closed_end'
        AND morningstar_id NOT IN (SELECT morningstar_id FROM fund_screener_pool
                                   WHERE region='US' GROUP BY morningstar_id HAVING COUNT(DISTINCT universe)>1)
        AND morningstar_id IN (SELECT morningstar_id FROM fund_screener_pool WHERE region='US' AND universe='FC')""")
    # 双标签行: 删除 FC/FO 组合中的 FC 污染腿（American Funds 类开放式）
    cur.execute("""DELETE FROM fund_screener_pool WHERE region='US' AND universe='FC'
        AND morningstar_id IN (SELECT morningstar_id FROM fund_screener_pool WHERE region='US'
            GROUP BY morningstar_id HAVING COUNT(DISTINCT universe)>1
                AND GROUP_CONCAT(DISTINCT universe) IN ('FC,FO','FO,FC'))""")
    con.commit()
    cur.execute("""SELECT COUNT(*) FROM fund f JOIN fund_screener_pool s
                   ON f.morningstar_id=s.morningstar_id WHERE s.region='US'""")
    tot = cur.fetchone()[0]
    cur.execute("""
        SELECT f.fund_type t, s.universe u FROM fund f
        JOIN fund_screener_pool s ON f.morningstar_id=s.morningstar_id
        WHERE s.region='US' AND s.universe IS NOT NULL""")
    OK = {'FE':'ETF','FO':'open_end','FC':'closed_end','CZ':'cit','SA':'separate_account'}
    bad = sum(1 for t, u in cur.fetchall() if OK.get(u) != t)
    print(f"[F2] mismatch={bad}/{tot}")
    assert bad == 0, "fund_type×universe 仍不一致!"


def rebuild_views(con):
    cur = con.cursor()
    cur.execute("DROP VIEW IF EXISTS v_fund_screen")
    cur.execute("""
    CREATE VIEW v_fund_screen AS
    SELECT f.fund_id, f.ticker, f.fund_name, f.morningstar_id, f.vehicle_mid,
           f.listing_level, f.fund_type, f.asset_class, f.domicile, f.currency,
           f.size_currency, f.size_usd, f.size_asof, f.launch_date,
           f.expense_ratio, f.is_leveraged
    FROM fund f
    WHERE f.listing_level='vehicle' AND f.vehicle_mid=f.morningstar_id""")
    cur.execute("DROP VIEW IF EXISTS v_holdings_latest")
    cur.execute("""
    CREATE VIEW v_holdings_latest AS
    SELECT h.* FROM fund_holdings_snapshot h
    JOIN (SELECT fund_id, MAX(as_of_date) maxd FROM fund_holdings_snapshot GROUP BY fund_id) m
      ON h.fund_id=m.fund_id AND h.as_of_date=m.maxd
    WHERE COALESCE(h.weight_quarantine,0)=0""")
    mm = " OR ".join([f"fc.category_value LIKE '%{c[:35]}%'" for c in MM_CATEGORIES]) or "0"
    cur.execute("DROP VIEW IF EXISTS v_fund_sharpe_clean")
    cur.execute(f"""
    CREATE VIEW v_fund_sharpe_clean AS
    SELECT r.*, f.fund_name, f.ticker
    FROM fund_risk_snapshot r JOIN fund f ON r.fund_id=f.fund_id
    WHERE r.sharpe_ratio IS NOT NULL AND ABS(r.sharpe_ratio)<={QA_SHARPE_CLEAN_BOUND}
      AND f.morningstar_id NOT IN (
          SELECT fc.fund_id FROM fund_category fc
          WHERE fc.dimension='morningstar_category' AND ({mm}))""")
    con.commit()
    print("[F3] views rebuilt")



def refresh_db_stats(con):
    """F5 (M7): 刷新 db_stats —— 文档唯一合法的统计数字来源, 根治硬编码漂移"""
    cur = con.cursor()
    for k, q in STATS_QUERIES.items():
        cur.execute(q)
        v = str(cur.fetchone()[0])
        cur.execute("INSERT INTO db_stats(stat_key,stat_value) VALUES (?,?) "
                    "ON CONFLICT(stat_key) DO UPDATE SET stat_value=excluded.stat_value, "
                    "updated_at=datetime('now')", (k, v))
    con.commit()


def cur2v(cur, q):
    cur.execute(q)
    return str(cur.fetchone()[0])


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    finalize_vehicles(con)
    try:
        fix_types(con)          # 仅US池有universe权威; EU/CNHK无跨标签问题
    except AssertionError as e:
        print("WARN:", e)
    rebuild_views(con)
    refresh_db_stats(con)
    con.close()
    print('[F5] db_stats refreshed')
