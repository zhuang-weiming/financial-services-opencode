# SCHEMA — fund_db.sqlite 语义与口径

> **分工**：表/列/视图的结构定义以 `pipeline/ddl_current.sql`（活库导出）为唯一权威；
> 本文件只记录 SQL 表达不了的东西——**字段语义、单位、护栏规则、datapoint 对照**。
> 统计数字一律查 DB `db_stats` 表，本文不写任何易变数值。

## 1. 实体关系

```
fund_company ──< fund >── fund_share_class
                 │ ├──< performance / risk / rating / category
                 │ ├──< holdings_snapshot (Top-10) · concentration(遗留)
                 │ └─── vehicle_mid ──> fund_listing_map
fund_screener_pool                统一候选池（region=US|EU|CN|HK; passed_filter: 1=已入库, 0=pending待拉取）
db_stats                          元数据：validate.py 自动刷新的 11 项计数
```

## 2. 关键字段语义

### fund

| 字段 | 口径 | 说明 |
|---|---|---|
| **size_usd** | USD (OF99A) | ★唯一跨基金可比规模 |
| fund_size_native | 本币 (OF009) | 必须配 size_currency 阅读；跨上市行会差 17~320 倍 |
| size_currency / size_asof | LS05M / OF010 | 币种实值 / 规模日期 |
| morningstar_id | — | `FEUSA*/F*/FOUSA*`=载体层；`0P*`=交易所上市层；UNIQUE 约束 |
| vehicle_mid / listing_level | — | 载体归并锚点 / `vehicle`\|`exchange_listing` |
| fund_type | universe 映射 | FE→ETF, FO→open_end, FC→closed_end |
| is_leveraged | MF01D | 杠杆产品标记（其高收益真实） |

### fund_holdings_snapshot

| 字段 | 说明 |
|---|---|
| weight_pct | Morningstar 原始值，可为负（空头） |
| is_notional=1 | 期货/互换/CFD 等名义敞口，权重可 >100%（真实） |
| weight_quarantine=1 | 单位级损坏行（非衍生品\|w\|>100% 或名义>500%），分析时排除 |

### fund_screener_pool（统一候选池）

| 列 | 说明 |
|---|---|
| region | US/EU/CN/HK/UK/IE/FR/CH/DE/IT/JP/TW/AU/SG（加值即扩区） |
| universe | FE/FO/FC（US 池使用；类型权威来源） |
| search_country | 筛选时用的 LS017 注册地 |
| **passed_filter** | **`1`=已准入且入库；`0`=pending 待拉取**——即 s2/s3 的工作集 |

> v1.4.2: 原 us100m/eu100m/cn_hk100m 三张区域表已合并至此并删除（行数守恒 22,268）。

### 遗留对象（仅登记，不建议使用）

`v_fund_snapshot`(兼容视图，fund_size_native 已带币种语境)、`fund_enriched`(旧宽表)、`fund_benchmark`、`fund_concentration`(仅原始786只)。

## 3. 护栏视图（分析入口）

| 视图 | 用途 | 内建过滤 |
|---|---|---|
| v_fund_screen | 规模筛选/排序唯一入口 | 仅载体级 + vehicle 自洽 |
| v_fund_sharpe_clean | Sharpe 排名 | 剔除货币基金伪影与 \|Sharpe\|>5 |
| v_holdings_latest | 最新持仓快照 | 每基金取 MAX(as_of_date)，排除隔离行 |

## 4. Datapoint 注册表（config.py 同步）

| ID | 含义 → 落库 |
|---|---|
| **OF99A** / OF010 / OF009 | USD规模→size_usd ★ / 规模日期→size_asof / 本币规模→fund_size_native |
| OS00F / LS05M / LS017 / MF01D / ZZ006 | 成立日期→launch_date / 币种→size_currency / 注册地→domicile / 杠杆→is_leveraged / 费率→expense_ratio |
| PM004·PM00A·PM00C | 收益 1M/YTD/1Y → performance |
| RR010·RR011·RR014 | Sharpe 1Y·3Y · 波动率 → risk_snapshot |
| RR01Y·MMR01·ESG48 | Star/Medalist/Sustainability → rating |
| OF003·HS05A·OF00C | 类别/风格箱/指数标记 → category |

## 5. QA 基线

15 条断言见 `pipeline/validate.py`（完整性、唯一性、类型一致、组内规模极差<5%、
QQQ≈$400-600B 等锚点抽查、持仓区间、香港腿存在、视图非空）。运行即刷新 db_stats。

## 6. 版本史（详情见 pipeline 各文件头注释）

- **v1.4.1** 08-23下午：一致性加固——唯一索引实体化、遗留视图安全化、passed_filter 落地、db_stats 机制、目录重构（删 archive/phase_1_ddl/poc_report；legacy 并入 ingest_raw；phase_1_data→source_data）、文档瘦身
- **v1.4** 08-23：修复采集期引入的 14 项数据质量问题（规模口径/重复行/缺HK腿/权重损坏/类型错配等），新增 6 列+1映射表+3护栏视图
- **v1.3 及以前**：初始 schema 与 Phase-1 入库（结构见 git 或 ddl 历史）
