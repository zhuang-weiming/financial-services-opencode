"""
s4_ingest.py — 幂等入库（唯一权威写入路径）
反污染规则（全部内建，缺一不可）:
  R1  fund.morningstar_id 部分UNIQUE索引 → 杜绝同mid多行 (历史#10)
  R2  size_usd 只来自 OF99A; fund_size(本币) 必须伴随 LS05M 实值 (历史#1/3/5)
  R3  currency/domicile 取 LS05M/LS017 实值，代码中无字面量默认 (历史#3)
  R4  INSERT 必含 launch_date←OS00F (历史#8)
  R5  fund_type 由 universe 权威映射，禁止推断漂移 (历史#7)
  R6  listing_level 由 mid 前缀判定 (0P*=exchange_listing) (历史#2)
  R7  持仓插入即计算 is_notional / weight_quarantine (历史#6)
  R8  全部子表 INSERT OR IGNORE / ON CONFLICT 幂等
用法: python3 s4_ingest.py --master <json> --region us|eu|cn_hk
"""
import argparse, json, sqlite3
from datetime import datetime, timezone
from config import (DB_PATH, DP, PERF_ASOF, RISK_ASOF, UNIVERSE_TO_FUND_TYPE,
                    LISTING_PREFIX, DERIVATIVE_KEYWORDS, SCREENER_TABLE, REGION_FILTER,
                    REGION_META, QUARANTINE_ABS_W_NONDERIV, QUARANTINE_ABS_W_NOTIONAL)

REGION_UNIVERSE = {"us": None, "eu": "FO", "cn_hk": "FO"}   # us由screener行自带uni


def ensure_constraints(cur):
    """R1: 唯一性约束（幂等创建）"""
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_fund_mid ON fund(morningstar_id)")


def gen_fund_id(cur, mid, ticker, prefix):
    if ticker:
        cur.execute("SELECT morningstar_id FROM fund WHERE fund_id=?", (ticker,))
        row = cur.fetchone()
        if row is None or row[0] == mid:
            return ticker
    return f"{prefix}_{mid[-8:]}"


def ingest_master(con, master: dict, region: str, default_fund_type: str = None):
    """
    master: {mid: {dp_id: value}}  —— 来自 s2 输出（已扁平化）
    """
    cur = con.cursor()
    ensure_constraints(cur)
    now = datetime.now(timezone.utc).isoformat()
    prefix = REGION_META[region][2]   # v1.5: fund_id 前缀来自 REGION_META
    ftype_default = default_fund_type  # v1.5: 由调用方显式给定(CIT/CEF等)

    # company 归属（v1.5: 按 REGION_META 动态确保）
    comp_key, jurisdiction, fid_prefix = REGION_META[region]
    cur.execute("""INSERT INTO fund_company
        (company_id, company_name_en, jurisdiction, data_source, created_at, updated_at)
        VALUES (?,?,?,?,?,?) ON CONFLICT(company_id) DO NOTHING""",
        (comp_key, "Unknown", jurisdiction, "morningstar_mcp", now, now))
    if default_fund_type is None:
        default_fund_type = UNIVERSE_TO_FUND_TYPE.get(UNIVERSE_DEFAULT.get(region, "FO"), "open_end")

    stats = dict(f=0, p=0, r=0, c=0, g=0)
    for mid, v in master.items():
        if not isinstance(v, dict):
            continue
        g = lambda k: v.get(DP[k])

        UNIVERSE_DEFAULT = {"us": "FO", "eu": "FO", "cn_hk": "FO"}   # legacy keys

# ---- R2/R3: 规模与币种实值 ----
        def _f(x):
            try: return float(x) if x not in (None, "") else None
            except (TypeError, ValueError): return None
        size_usd   = _f(g("size_usd"))
        size_nat   = _f(g("size_native"))
        currency   = g("currency") or None          # R3: 无默认字面量
        domicile   = g("domicile") or None
        launch     = str(g("inception"))[:10] if g("inception") else None   # R4
        lev        = 1 if str(g("leveraged") or "").lower() in ("yes","true","1") else 0
        ap         = "passive" if str(g("index_flag") or "").lower() == "yes" else "active"

        cur.execute("SELECT fund_id FROM fund WHERE morningstar_id=?", (mid,))
        row = cur.fetchone()
        if row is None:
            # 名称/ticker 从 screener 池取（池是名字的权威来源）
            cur.execute(f"""SELECT fund_name, ticker FROM {SCREENER_TABLE}
                             WHERE morningstar_id=? AND {REGION_FILTER[region]}""", (mid,))
            sr = cur.fetchone()
            name = (sr[0] if sr and sr[0] else mid)
            ticker = (sr[1] if sr and sr[1] else "")
            fid = gen_fund_id(cur, mid, ticker, fid_prefix)
            level = "exchange_listing" if str(mid).startswith(LISTING_PREFIX) else "vehicle"  # R6
            cur.execute("""
                INSERT INTO fund (fund_id, fund_code, ticker, morningstar_id, fund_name,
                    fund_short_name, company_id, fund_type, asset_class, domicile, currency,
                    active_passive, expense_ratio, fund_size, size_asof,
                    size_currency, size_usd, is_leveraged,
                    vehicle_mid, listing_level, launch_date,
                    data_source, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'morningstar_mcp',?,?)
                ON CONFLICT(morningstar_id) DO NOTHING""",
                (fid, fid, ticker or None, mid, name, name[:50], comp_key,
                 ftype_default, "equity", domicile, currency, ap,
                 _f(g("expense")), size_nat,
                 str(g("size_asof"))[:10] if g("size_asof") else PERF_ASOF,
                 currency, size_usd, lev, mid, level, launch, now, now))
            if cur.rowcount:
                stats["f"] += 1
            cur.execute("SELECT fund_id FROM fund WHERE morningstar_id=?", (mid,))
            fid = cur.fetchone()[0]
            cur.execute("""INSERT INTO fund_share_class
                (share_class_id, fund_id, is_active, data_source, created_at)
                VALUES (?,?,1,'morningstar_mcp',?)
                ON CONFLICT(share_class_id) DO NOTHING""", (f"{fid}-SC", fid, now))
        else:
            fid = row[0]
            # 已存在：仅回填空值字段（不覆盖既有权威值）
            cur.execute("""UPDATE fund SET
                size_currency=COALESCE(size_currency,?), size_usd=COALESCE(size_usd,?),
                size_asof=COALESCE(size_asof,?), launch_date=COALESCE(launch_date,?),
                domicile=COALESCE(domicile,?), currency=COALESCE(currency,?),
                is_leveraged=CASE WHEN is_leveraged IS NULL THEN ? ELSE is_leveraged END,
                updated_at=? WHERE morningstar_id=?""",
                (currency, size_usd,
                 str(g("size_asof"))[:10] if g("size_asof") else None,
                 launch, domicile, currency, lev, now, mid))

        # ---- 子表（R8 幂等）----
        for period, key in [("1M","ret_1m"), ("YTD","ret_ytd"), ("1Y","ret_1y")]:
            val = _f(g(key))
            if val is not None:
                cur.execute("""INSERT INTO fund_performance_snapshot
                    (fund_id, asof_date, period, return_pct, annualized_return, data_source)
                    VALUES (?,?,?,?,?, 'morningstar_mcp')
                    ON CONFLICT(fund_id, period, asof_date) DO UPDATE SET return_pct=excluded.return_pct""",
                    (fid, PERF_ASOF, period, val, val if period == "1Y" else None))
                stats["p"] += 1
        s_sharpe, s_vol = _f(g("sharpe_1y")), _f(g("stddev_1y"))
        if s_sharpe is not None or s_vol is not None:
            cur.execute("""INSERT INTO fund_risk_snapshot
                (fund_id, asof_date, window, sharpe_ratio, volatility_annual, data_source)
                VALUES (?, ?, '1Y', ?, ?, 'morningstar_mcp')
                ON CONFLICT(fund_id, window, asof_date) DO UPDATE SET
                    sharpe_ratio=excluded.sharpe_ratio, volatility_annual=excluded.volatility_annual""",
                (fid, RISK_ASOF, s_sharpe, s_vol))
            stats["r"] += 1
        for dim, key in [("morningstar_category","category"), ("style_box","style_box"),
                         ("is_index_fund","index_flag")]:
            val = g(key)
            if val not in (None, ""):
                cur.execute("""INSERT INTO fund_category
                    (fund_id, dimension, category_value, category_source, is_primary,
                     effective_date, data_source)
                    VALUES (?,?,?,'morningstar',1,?,'morningstar_mcp')
                    ON CONFLICT(fund_id, dimension, category_value, effective_date) DO NOTHING""",
                    (fid, dim, str(val), PERF_ASOF))
                stats["c"] += 1
        for key, rt in [("star","Star Rating"), ("medalist","Medalist Rating"),
                        ("sustainability","Sustainability Rating")]:
            val = g(key)
            if val not in (None, ""):
                cur.execute("""INSERT INTO fund_rating
                    (fund_id, agency, rating_type, rating_value, rating_date, data_source)
                    VALUES (?,'Morningstar',?,?,?,'morningstar_mcp')
                    ON CONFLICT(fund_id, agency, rating_type, rating_date) DO UPDATE SET
                        rating_value=excluded.rating_value""",
                    (fid, rt, str(val), PERF_ASOF))
                stats["g"] += 1
    con.commit()
    print(f"[{region}] funds+{stats['f']} perf+{stats['p']} risk+{stats['r']} "
          f"cat+{stats['c']} rating+{stats['g']}")


def ingest_holdings(con, holdings: dict):
    """holdings: {mid: {'as_of_date':..,'holdings':[{morningstar_id,holding_name,holding_weight}]}}
    R7: 插入时即做衍生品识别与隔离"""
    cur = con.cursor()
    ensure_constraints(cur)
    n_ins = n_notional = n_quar = 0
    for mid, pack in holdings.items():
        cur.execute("SELECT fund_id FROM fund WHERE morningstar_id=?", (mid,))
        row = cur.fetchone()
        if not row:
            continue
        fid = row[0]
        for h in pack.get("holdings", []):
            nm = str(h.get("holding_name") or "")[:100]
            w = h.get("holding_weight")
            try:
                w = float(w) if w is not None else None
            except (TypeError, ValueError):
                w = None
            is_not = int(any(k in nm for k in DERIVATIVE_KEYWORDS))
            quar = 0
            if w is not None:
                if is_not and abs(w) > QUARANTINE_ABS_W_NOTIONAL:
                    quar = 1
                if (not is_not) and abs(w) > QUARANTINE_ABS_W_NONDERIV:
                    quar = 1
            cur.execute("""
                INSERT INTO fund_holdings_snapshot
                    (fund_id, as_of_date, morningstar_security_id, security_name,
                     weight_pct, is_top10, data_source, created_at,
                     is_notional, weight_quarantine)
                VALUES (?,?,?,?,?,1,'morningstar_mcp',datetime('now'),?,?)
                ON CONFLICT(fund_id, as_of_date, morningstar_security_id) DO NOTHING""",
                (fid, pack.get("as_of_date") or "", h.get("morningstar_id") or "",
                 nm, w, is_not, quar))
            if cur.rowcount:
                n_ins += 1
                n_notional += is_not
                n_quar += quar
    con.commit()
    print(f"[holdings] +{n_ins} rows (notional={n_notional}, quarantined={n_quar})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--master");  ap.add_argument("--region")
    ap.add_argument("--holdings")
    a = ap.parse_args()
    con = sqlite3.connect(DB_PATH)
    if a.master:
        with open(a.master) as f:
            raw = json.load(f)
        # 兼容两种输入: {mid:{dp:val}} 或 {mid:{'values':[{datapointId,value}]}}
        flat = {}
        for mid, d in raw.items():
            if isinstance(d, dict) and "values" in d:
                flat[mid] = {x["datapointId"]: x.get("value") for x in d["values"]}
            else:
                flat[mid] = d
        ingest_master(con, flat, a.region)
    if a.holdings:
        with open(a.holdings) as f:
            ingest_holdings(con, json.load(f))
    con.close()
