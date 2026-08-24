"""
config.py — Fund DB 管道唯一配置源
与 fund_db.sqlite v1.4 严格一致。任何口径变更必须先改这里。
"""
from pathlib import Path

# ---------- 路径 ----------
BASE_DIR = Path(__file__).resolve().parent.parent          # data/fund_db/
DB_PATH = BASE_DIR / "fund_db.sqlite"
RAW_DIR = BASE_DIR / "ingest_raw" / "phase2_current"        # 新拉取落地（带日期子目录）
ARCHIVE_DIR = BASE_DIR / "ingest_raw_legacy"
TOKEN_FILE = Path("/tmp/morningstar_token.json")

# ---------- MCP ----------
MCP_URL = "https://mcp.morningstar.com/mcp"
CLIENT_INFO = {"name": "fund-loader", "version": "1.0.0"}
BATCH_SIZE = 10                 # morningstar-data-tool 单批上限经验值
HOLDINGS_BATCH = 10             # fund-holdings-tool 上限 10 ids/次
TOP_N_HOLDINGS = 10
CHECKPOINT_EVERY_BATCHES = 25   # 每25批落盘checkpoint
SLEEP_BETWEEN_CALLS = 0.2

# ---------- Datapoint 注册表（唯一权威，见 schema §6）----------
DP = {
    "size_usd":      "OF99A",   # ★ 权威美元规模
    "size_asof":     "OF010",
    "size_native":   "OF009",   # 本币规模(仅参考)
    "inception":     "OS00F",
    "currency":      "LS05M",
    "domicile":      "LS017",
    "leveraged":     "MF01D",
    "expense":       "ZZ006",
    "ret_1m":        "PM004",
    "ret_ytd":       "PM00A",
    "ret_1y":        "PM00C",
    "category":      "OF003",
    "style_box":     "HS05A",
    "index_flag":    "OF00C",
    "sharpe_1y":     "RR010",
    "sharpe_3y":     "RR011",
    "stddev_1y":     "RR014",
    "star":          "RR01Y",
    "medalist":      "MMR01",
    "sustainability":"ESG48",
}
DP_FUND_MASTER = [DP["size_usd"], DP["size_asof"], DP["size_native"], DP["inception"],
                  DP["currency"], DP["domicile"], DP["leveraged"], DP["expense"],
                  DP["ret_1m"], DP["ret_ytd"], DP["ret_1y"], DP["category"],
                  DP["style_box"], DP["index_flag"],
                  DP["sharpe_1y"], DP["stddev_1y"],
                  DP["star"], DP["medalist"], DP["sustainability"]]

# ---------- Screener 统一候选池（v1.4.2 合并三张区域表）----------
SCREENER_TABLE = "fund_screener_pool"
# region 键 -> SQL 过滤片段（cn_hk 腿拆为 CN/HK 两区）
REGION_FILTER = {
    "us":    "region='US'",
    "eu":    "region='EU'",
    "cn_hk": "region IN ('CN','HK')",
    # v1.5 扩张区域
    "uk":    "region='UK'",
    "ie":    "region='IE'",
    "eu4":   "region IN ('FR','CH','DE','IT')",
    "apac4": "region IN ('JP','TW','AU','SG')",
    # 单国键 (v1.5 eu4/apac 分桶入库使用)
    "fr": "region='FR'", "ch": "region='CH'", "de": "region='DE'", "it": "region='IT'",
    "jp": "region='JP'", "tw": "region='TW'", "au": "region='AU'", "sg": "region='SG'",
}

# 区域 -> (fund_company 键, 辖区标签, fund_id 前缀)
REGION_META = {
    "us":    ("CMP_MCP_US",   "United States",        "M"),
    "eu":    ("CMP_MCP_EU",   "Luxembourg",           "EU"),
    "cn_hk": ("CMP_MCP_CNHK", "China/Hong Kong",      "CN"),
    "uk":    ("CMP_MCP_UK",   "United Kingdom",       "UK"),
    "ie":    ("CMP_MCP_IE",   "Ireland",              "IE"),
    "fr":    ("CMP_MCP_FR",   "France",               "FR"),
    "ch":    ("CMP_MCP_CH",   "Switzerland",          "CH"),
    "de":    ("CMP_MCP_DE",   "Germany",              "DE"),
    "it":    ("CMP_MCP_IT",   "Italy",                "IT"),
    "jp":    ("CMP_MCP_JP",   "Japan",                "JP"),
    "tw":    ("CMP_MCP_TW",   "Taiwan",               "TW"),
    "au":    ("CMP_MCP_AU",   "Australia",            "AU"),
    "sg":    ("CMP_MCP_SG",   "Singapore",            "SG"),
}
# passed_filter 语义: 1=已准入且入库 | 0=候选待拉取(pending 工作集)

# ---------- 快照口径常量 ----------
PERF_ASOF = "2026-07-31"
RISK_ASOF = "2026-07-31"

# ---------- Screener 池定义 ----------
EU_DOMICILES = ["Luxembourg"]            # v1.0 仅卢森堡；扩展爱尔兰/英国时在此追加
CNHK_COUNTRIES = ["China", "Hong Kong"]  # 修复#4: 两腿都必须跑完，禁止提前break
SIZE_THRESHOLD_NATIVE = 100_000_000      # >1亿(本币: USD/EUR/HKD/CNY)
MIN_AGE_YEARS = 1.0

# ---------- 反污染规则 ----------
UNIVERSE_TO_FUND_TYPE = {"FE": "ETF", "FO": "open_end", "FC": "closed_end",
                         "CZ": "cit", "SA": "separate_account"}
VEHICLE_PREFIX_PRIORITY = ["FEUSA", "F00000", "FOUSA", "FCUSA"]   # 载体层优先级
LISTING_PREFIX = "0P"                                             # 交易所上市层
DERIVATIVE_KEYWORDS = ["Future", "Swap", "CFD", "Cfd", "Forward",
                       "FUT ", "Total Return Swap", "Repo", "Recv"]
QUARANTINE_ABS_W_NONDERIV = 100.0   # 非衍生品 |w|>100% → 隔离
QUARANTINE_ABS_W_NOTIONAL = 500.0   # 衍生品 |w|>500% → 隔离复核

# ---------- db_stats 注册表 (M7: 文档唯一统计数字来源) ----------
STATS_QUERIES = {
    "fund_rows":         "SELECT COUNT(*) FROM fund",
    "unique_vehicles":   "SELECT COUNT(DISTINCT vehicle_mid) FROM fund",
    "listing_map":       "SELECT COUNT(*) FROM fund_listing_map",
    "holdings_rows":     "SELECT COUNT(*) FROM fund_holdings_snapshot",
    "performance_rows":  "SELECT COUNT(*) FROM fund_performance_snapshot",
    "risk_rows":         "SELECT COUNT(*) FROM fund_risk_snapshot",
    "rating_rows":       "SELECT COUNT(*) FROM fund_rating",
    "pool_us":           "SELECT COUNT(*) FROM fund_screener_pool WHERE region='US'",
    "pool_eu":           "SELECT COUNT(*) FROM fund_screener_pool WHERE region='EU'",
    "pool_cn":           "SELECT COUNT(*) FROM fund_screener_pool WHERE region='CN'",
    "pool_hk":           "SELECT COUNT(*) FROM fund_screener_pool WHERE region='HK'",
    "size_usd_coverage": "SELECT printf('%.1f%%', 100.0*SUM(size_usd IS NOT NULL)/COUNT(*)) FROM fund",
}

# ---------- QA 基线 (validate.py) ----------
SIZE_CLUSTER_REL = 0.02                  # 车辆聚类阈值(相对max): 真实跨上市组实测~0%
QA_MAX_SPAN_PCT_IN_LISTING_GROUP = 5.0   # QA断言上限(留安全边际)
QA_SHARPE_CLEAN_BOUND = 5.0

def dated_raw_subdir(tag: str) -> Path:
    """按日期落盘: ingest_raw/phase2_current/YYYYMMDD_<tag>/"""
    import datetime as _dt
    d = RAW_DIR / f"{_dt.date.today():%Y%m%d}_{tag}"
    d.mkdir(parents=True, exist_ok=True)
    return d
