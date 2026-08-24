-- ══════════════════════════════════════════════════════════
-- ddl_current.sql — 权威 Schema（从 fund_db.sqlite v1.4 实况导出）
-- 导出日期: 2026-08-23 | 工具: pipeline/export_ddl
-- 关系说明: 此文件为导出快照; 结构变更请走迁移脚本后重新导出。
-- 历史 phase_1_ddl/(v1.3) 已删除——缺 v1.4 列与唯一索引，属污染复发模板。
-- ══════════════════════════════════════════════════════════





-- ── Tables ──

CREATE TABLE db_stats (
    stat_key VARCHAR(50) PRIMARY KEY, stat_value TEXT,
    updated_at TIMESTAMP DEFAULT (datetime('now')));

CREATE TABLE fund (
    fund_id             VARCHAR(20)  PRIMARY KEY,
    fund_code           VARCHAR(20)  NOT NULL,            -- 销售代码 / ticker
    ticker              VARCHAR(20),                      -- Morningstar + FactSet
    morningstar_id      VARCHAR(20),                      -- Morningstar id-lookup
    fund_name           VARCHAR(200) NOT NULL,            -- FactSet summary
    fund_short_name     VARCHAR(50)  NOT NULL,
    company_id          VARCHAR(20)  NOT NULL,
    fund_type           VARCHAR(30)  NOT NULL,            -- open_end / closed_end / ETF
    asset_class         VARCHAR(30),                      -- equity / FI / multi_asset
    vehicle_type        VARCHAR(30),                      -- SICAV / UCITS / Trust / LLC
    domicile            CHAR(3)      NOT NULL,            -- ISO
    launch_date         DATE,                              -- 改 nullable：FactSet 401 时无源
    currency            CHAR(3)      NOT NULL,
    active_passive      VARCHAR(10)  NOT NULL,            -- active / passive / enhanced
    benchmark_id        VARCHAR(20),                      -- FK → fund_benchmark
    expense_ratio       DECIMAL(6,4),                     -- Morningstar ZZ006/OS05P/OS00M
    fund_size           DECIMAL(18,2),                    -- Morningstar OF009（基金级）
    size_asof           DATE,                              -- Morningstar OF010
    status              VARCHAR(20)  NOT NULL DEFAULT 'active',  -- active / inactive
    data_source         VARCHAR(50)  NOT NULL DEFAULT 'mixed',
    created_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    updated_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now')), size_currency VARCHAR(30), size_usd DECIMAL(20,2), is_leveraged BOOLEAN, vehicle_mid VARCHAR(30), listing_level VARCHAR(20),
    FOREIGN KEY (company_id)   REFERENCES fund_company(company_id) ON DELETE RESTRICT,
    FOREIGN KEY (benchmark_id) REFERENCES fund_benchmark(benchmark_id) ON DELETE RESTRICT
);

CREATE TABLE fund_benchmark (
    benchmark_id        VARCHAR(20)  PRIMARY KEY,
    benchmark_code      VARCHAR(20)  NOT NULL,
    benchmark_name      VARCHAR(200) NOT NULL,
    index_provider      VARCHAR(50),                     -- Morningstar LI055
    asset_class         VARCHAR(30)  NOT NULL,            -- equity/fixed_income/multi_asset/commodity
    currency            CHAR(3)      NOT NULL,
    data_source         VARCHAR(50)  NOT NULL DEFAULT 'mixed',
    created_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    updated_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE fund_category (
    category_id         INTEGER      PRIMARY KEY AUTOINCREMENT,
    fund_id             VARCHAR(20)  NOT NULL,
    dimension           VARCHAR(30)  NOT NULL,             -- morningstar_category / style_box / is_retail_eligible / is_index_fund / is_leveraged
    category_value      VARCHAR(50)  NOT NULL,
    category_source     VARCHAR(30)  NOT NULL DEFAULT 'morningstar',
    is_primary          BOOLEAN      NOT NULL DEFAULT 1,
    effective_date      DATE          NOT NULL,
    expiry_date         DATE,
    data_source         VARCHAR(50)  NOT NULL DEFAULT 'morningstar',
    created_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fund_id) REFERENCES fund(fund_id) ON DELETE CASCADE,
    UNIQUE (fund_id, dimension, category_value, effective_date)
);

CREATE TABLE fund_company (
    company_id          VARCHAR(20)  PRIMARY KEY,           -- 业务生成，如 BCK0001
    company_name_en     VARCHAR(100) NOT NULL,            -- Morningstar OF006
    company_name_cn     VARCHAR(100),                     -- 手工（暂不入库）
    jurisdiction        CHAR(3)      NOT NULL,            -- ISO 3166
    regulatory_body     VARCHAR(50),                      -- 手工（无 MCP 源）
    license_type        VARCHAR(50),                      -- 手工
    ownership_type      VARCHAR(30),                      -- 手工
    established_date    DATE,                              -- FactSet EntityReference（无 entitlement，预留）
    aum_total           DECIMAL(18,2),                    -- Morningstar OF009（公司级聚合）
    aum_currency        CHAR(3),                          -- 默认 USD
    aum_asof            DATE,                              -- Morningstar OF010
    listed              BOOLEAN,                          -- FactSet（无 entitlement，预留）
    data_source         VARCHAR(50)  NOT NULL DEFAULT 'mixed',
    created_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    updated_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE fund_concentration (
    concentration_id  INTEGER      PRIMARY KEY AUTOINCREMENT,
    fund_id           VARCHAR(20)  NOT NULL,
    as_of_date        DATE          NOT NULL,
    top1_pct          DECIMAL(6,2) NOT NULL,
    top5_pct          DECIMAL(6,2) NOT NULL,
    top10_pct         DECIMAL(6,2) NOT NULL,
    hhi               DECIMAL(8,4) NOT NULL,             -- Herfindahl 指数
    num_holdings      INT,                                -- 总持仓数
    data_source       VARCHAR(50)  NOT NULL DEFAULT 'derived',
    created_at        TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fund_id) REFERENCES fund(fund_id) ON DELETE CASCADE,
    UNIQUE (fund_id, as_of_date)
);

CREATE TABLE fund_enriched (
    morningstar_id     VARCHAR(30) PRIMARY KEY,
    universe           VARCHAR(5),
    fund_name          VARCHAR(200),
    ticker             VARCHAR(20),
    morningstar_category VARCHAR(100),
    -- 关键筛选字段
    fund_size          DECIMAL(20,4),     -- OF009 基金总规模
    size_asof          DATE,
    has_top10_holdings INTEGER DEFAULT 0, -- 是否有 top10 持仓
    -- 其他 datapoints（后续扩展）
    expense_ratio      DECIMAL(8,4),
    launch_date        DATE,
    -- 元数据
    data_source        VARCHAR(50) DEFAULT 'morningstar',
    created_at         TIMESTAMP DEFAULT (datetime('now')),
    -- 筛选标记
    passed_filter      INTEGER DEFAULT 0  -- 1 = 同时有 size + top10
);

CREATE TABLE fund_holdings_snapshot (
    holding_id                 INTEGER      PRIMARY KEY AUTOINCREMENT,
    fund_id                    VARCHAR(20)  NOT NULL,
    as_of_date                 DATE          NOT NULL,
    morningstar_security_id    VARCHAR(20)  NOT NULL,     -- Morningstar 内部证券 ID
    security_name              VARCHAR(100) NOT NULL,
    weight_pct                 DECIMAL(10,4) NOT NULL,
    is_top10                   BOOLEAN      NOT NULL DEFAULT 0,
    data_source                VARCHAR(50)  NOT NULL DEFAULT 'morningstar_fund_holdings_tool',
    created_at                 TIMESTAMP   NOT NULL DEFAULT (datetime('now')), is_notional BOOLEAN, weight_quarantine BOOLEAN,
    FOREIGN KEY (fund_id) REFERENCES fund(fund_id) ON DELETE CASCADE,
    UNIQUE (fund_id, as_of_date, morningstar_security_id)
);

CREATE TABLE fund_listing_map (
    listing_mid     VARCHAR(30) PRIMARY KEY,
    vehicle_mid     VARCHAR(30),
    match_method    VARCHAR(30),   -- 'id_lookup' | 'ticker' | 'name' | 'self'
    confidence      VARCHAR(10),   -- high/medium/low
    created_at      TIMESTAMP DEFAULT (datetime('now'))
);

CREATE TABLE fund_performance_snapshot (
    perf_id            INTEGER      PRIMARY KEY AUTOINCREMENT,
    fund_id            VARCHAR(20)  NOT NULL,
    asof_date          DATE          NOT NULL,
    period             VARCHAR(10)  NOT NULL,             -- 1M / 3M / 6M / YTD / 1Y / 3Y / 5Y
    return_pct         DECIMAL(10,4) NOT NULL,
    annualized_return  DECIMAL(10,4),                     -- ≥ 1Y 区间必填
    data_source        VARCHAR(50)  NOT NULL DEFAULT 'morningstar',
    created_at         TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fund_id) REFERENCES fund(fund_id) ON DELETE CASCADE,
    UNIQUE (fund_id, period, asof_date)
);

CREATE TABLE fund_rating (
    rating_id      INTEGER      PRIMARY KEY AUTOINCREMENT,
    fund_id        VARCHAR(20)  NOT NULL,
    agency         VARCHAR(30)  NOT NULL DEFAULT 'Morningstar',
    rating_type    VARCHAR(30)  NOT NULL,                 -- Star Rating / Medalist Rating / Sustainability Rating
    rating_value   VARCHAR(20)  NOT NULL,                 -- 1-5 / Gold-Silver-Bronze / Low-High
    rating_score   DECIMAL(8,4),                         -- 可选量化得分
    rating_date    DATE          NOT NULL,
    data_source    VARCHAR(50)  NOT NULL DEFAULT 'morningstar',
    created_at     TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fund_id) REFERENCES fund(fund_id) ON DELETE CASCADE,
    UNIQUE (fund_id, agency, rating_type, rating_date),
    CHECK (agency = 'Morningstar'),                        -- 限定枚举
    CHECK (rating_type IN ('Star Rating', 'Medalist Rating', 'Sustainability Rating'))
);

CREATE TABLE fund_risk_snapshot (
    risk_id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    fund_id              VARCHAR(20)  NOT NULL,
    asof_date            DATE          NOT NULL,
    window               VARCHAR(10)  NOT NULL,            -- 1Y / 3Y
    sharpe_ratio         DECIMAL(8,4) NOT NULL,
    volatility_annual    DECIMAL(8,4) NOT NULL,
    data_source          VARCHAR(50)  NOT NULL DEFAULT 'morningstar',
    created_at           TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fund_id) REFERENCES fund(fund_id) ON DELETE CASCADE,
    UNIQUE (fund_id, window, asof_date)
);

CREATE TABLE fund_screener_pool (
    pool_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    region              VARCHAR(10) NOT NULL,      -- US | EU | CN | HK | (未来: EU_IE...)
    morningstar_id      VARCHAR(30) NOT NULL,
    universe            VARCHAR(5),                -- FE/FO/FC (主要US使用)
    fund_name           VARCHAR(200),
    ticker              VARCHAR(20),
    morningstar_category VARCHAR(100),
    net_asset_value     DECIMAL(20,4),
    last_price          DECIMAL(20,4),
    exchange            VARCHAR(50),
    medalist_rating     VARCHAR(20),
    fund_size_native    DECIMAL(20,4),
    fund_size_usd       DECIMAL(20,4),
    size_currency       VARCHAR(10),
    currency            VARCHAR(10),
    search_country      VARCHAR(50),               -- 筛选时用的 LS017 值
    passed_filter       BOOLEAN,
    fetched_at          TIMESTAMP DEFAULT (datetime('now')),
    UNIQUE(region, morningstar_id)
);

CREATE TABLE fund_share_class (
    share_class_id      VARCHAR(20)  PRIMARY KEY,
    fund_id             VARCHAR(20)  NOT NULL,
    share_class_letter  CHAR(1),                         -- A/C/I/Y/H/ETF（来自 Morningstar LS012）
    share_class_name    VARCHAR(50),                     -- FactSet summary `shareClass`
    is_active           BOOLEAN      NOT NULL DEFAULT 1,
    data_source         VARCHAR(50)  NOT NULL DEFAULT 'mixed',
    created_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    updated_at          TIMESTAMP   NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fund_id) REFERENCES fund(fund_id) ON DELETE CASCADE
);

CREATE TABLE sqlite_sequence(name,seq);

-- ── Views ──

CREATE VIEW v_fund_screen AS
    SELECT f.fund_id, f.ticker, f.fund_name, f.morningstar_id, f.vehicle_mid,
           f.listing_level, f.fund_type, f.asset_class, f.domicile, f.currency,
           f.size_currency, f.size_usd, f.size_asof, f.launch_date,
           f.expense_ratio, f.is_leveraged
    FROM fund f
    WHERE f.listing_level='vehicle' AND f.vehicle_mid=f.morningstar_id;

CREATE VIEW v_fund_sharpe_clean AS
    SELECT r.*, f.fund_name, f.ticker
    FROM fund_risk_snapshot r JOIN fund f ON r.fund_id=f.fund_id
    WHERE r.sharpe_ratio IS NOT NULL AND ABS(r.sharpe_ratio)<=5.0
      AND f.morningstar_id NOT IN (
          SELECT fc.fund_id FROM fund_category fc
          WHERE fc.dimension='morningstar_category' AND (fc.category_value LIKE '%Money Market-Taxable%' OR fc.category_value LIKE '%Prime Money Market%'));

CREATE VIEW v_fund_snapshot AS
WITH
  -- 每只基金每个 period 最新 asof_date
  latest_perf AS (
      SELECT fund_id, period, MAX(asof_date) AS max_asof
      FROM fund_performance_snapshot
      GROUP BY fund_id, period
  ),
  -- 每只基金每个 window 最新 asof_date
  latest_risk AS (
      SELECT fund_id, window, MAX(asof_date) AS max_asof
      FROM fund_risk_snapshot
      GROUP BY fund_id, window
  ),
  -- 每只基金最新集中度日期
  latest_conc AS (
      SELECT fund_id, MAX(as_of_date) AS max_asof
      FROM fund_concentration
      GROUP BY fund_id
  ),
  -- 每只基金每个 rating_type 最新评级日
  latest_rating AS (
      SELECT fund_id, rating_type, MAX(rating_date) AS max_date
      FROM fund_rating
      GROUP BY fund_id, rating_type
  ),
  -- 当前有效的主分类
  primary_category AS (
      SELECT fund_id, dimension, category_value
      FROM fund_category
      WHERE is_primary = 1 AND expiry_date IS NULL
  )
SELECT
    f.fund_id,
    f.fund_name,
    f.fund_short_name,
    f.company_id,
    c.company_name_en,
    f.fund_type,
    f.asset_class,
    f.domicile,
    f.currency,
    f.launch_date,
    f.status,
    f.expense_ratio,
    f.fund_size AS fund_size_native,   -- 本币口径! 必须配 size_currency 阅读
    f.size_currency,
    f.size_usd,                        -- ★ 权威跨基金可比口径 (OF99A)
    f.size_asof,
    f.size_asof,
    f.active_passive,
    -- 业绩快照（最新，9 个 period）
    p1m.return_pct    AS return_1m,
    pYTD.return_pct   AS return_ytd,
    p1y.return_pct    AS return_1y,
    p2y.return_pct    AS return_2y,
    p3y.return_pct    AS return_3y,
    p5y.return_pct    AS return_5y,
    p10y.return_pct   AS return_10y,
    p15y.return_pct   AS return_15y,
    p20y.return_pct   AS return_20y,
    -- 风险快照（最新 1Y）
    r1y.sharpe_ratio,
    r1y.volatility_annual,
    -- 集中度（最新）
    conc.top10_pct,
    conc.hhi,
    -- 评级
    rs.rating_value   AS morningstar_star,
    rmedal.rating_value AS medalist_rating,
    resg.rating_value   AS sustainability_rating,
    -- 主分类
    cat_cat.category_value    AS morningstar_category,
    cat_style.category_value  AS style_box,
    cat_retail.category_value AS is_retail_eligible,
    cat_index.category_value  AS is_index_fund,
    cat_leverage.category_value AS is_leveraged,
    -- 审计
    f.data_source,
    f.updated_at
FROM fund f
JOIN fund_company c ON f.company_id = c.company_id
-- 业绩 1M
LEFT JOIN latest_perf lp1m ON lp1m.fund_id = f.fund_id AND lp1m.period = '1M'
LEFT JOIN fund_performance_snapshot p1m
    ON p1m.fund_id = lp1m.fund_id
    AND p1m.period = lp1m.period
    AND p1m.asof_date = lp1m.max_asof
-- 业绩 YTD
LEFT JOIN latest_perf lpYTD ON lpYTD.fund_id = f.fund_id AND lpYTD.period = 'YTD'
LEFT JOIN fund_performance_snapshot pYTD
    ON pYTD.fund_id = lpYTD.fund_id
    AND pYTD.period = lpYTD.period
    AND pYTD.asof_date = lpYTD.max_asof
-- 业绩 1Y
LEFT JOIN latest_perf lp1y ON lp1y.fund_id = f.fund_id AND lp1y.period = '1Y'
LEFT JOIN fund_performance_snapshot p1y
    ON p1y.fund_id = lp1y.fund_id
    AND p1y.period = lp1y.period
    AND p1y.asof_date = lp1y.max_asof
-- 业绩 2Y
LEFT JOIN latest_perf lp2y ON lp2y.fund_id = f.fund_id AND lp2y.period = '2Y'
LEFT JOIN fund_performance_snapshot p2y
    ON p2y.fund_id = lp2y.fund_id
    AND p2y.period = lp2y.period
    AND p2y.asof_date = lp2y.max_asof
-- 业绩 3Y
LEFT JOIN latest_perf lp3y ON lp3y.fund_id = f.fund_id AND lp3y.period = '3Y'
LEFT JOIN fund_performance_snapshot p3y
    ON p3y.fund_id = lp3y.fund_id
    AND p3y.period = lp3y.period
    AND p3y.asof_date = lp3y.max_asof
-- 业绩 5Y
LEFT JOIN latest_perf lp5y ON lp5y.fund_id = f.fund_id AND lp5y.period = '5Y'
LEFT JOIN fund_performance_snapshot p5y
    ON p5y.fund_id = lp5y.fund_id
    AND p5y.period = lp5y.period
    AND p5y.asof_date = lp5y.max_asof
-- 业绩 10Y
LEFT JOIN latest_perf lp10y ON lp10y.fund_id = f.fund_id AND lp10y.period = '10Y'
LEFT JOIN fund_performance_snapshot p10y
    ON p10y.fund_id = lp10y.fund_id
    AND p10y.period = lp10y.period
    AND p10y.asof_date = lp10y.max_asof
-- 业绩 15Y
LEFT JOIN latest_perf lp15y ON lp15y.fund_id = f.fund_id AND lp15y.period = '15Y'
LEFT JOIN fund_performance_snapshot p15y
    ON p15y.fund_id = lp15y.fund_id
    AND p15y.period = lp15y.period
    AND p15y.asof_date = lp15y.max_asof
-- 业绩 20Y
LEFT JOIN latest_perf lp20y ON lp20y.fund_id = f.fund_id AND lp20y.period = '20Y'
LEFT JOIN fund_performance_snapshot p20y
    ON p20y.fund_id = lp20y.fund_id
    AND p20y.period = lp20y.period
    AND p20y.asof_date = lp20y.max_asof
-- 风险 1Y
LEFT JOIN latest_risk lr1y ON lr1y.fund_id = f.fund_id AND lr1y.window = '1Y'
LEFT JOIN fund_risk_snapshot r1y
    ON r1y.fund_id = lr1y.fund_id
    AND r1y.window = lr1y.window
    AND r1y.asof_date = lr1y.max_asof
-- 集中度
LEFT JOIN latest_conc lconc ON lconc.fund_id = f.fund_id
LEFT JOIN fund_concentration conc
    ON conc.fund_id = lconc.fund_id
    AND conc.as_of_date = lconc.max_asof
-- Star Rating
LEFT JOIN latest_rating lrs ON lrs.fund_id = f.fund_id AND lrs.rating_type = 'Star Rating'
LEFT JOIN fund_rating rs
    ON rs.fund_id = lrs.fund_id
    AND rs.rating_type = lrs.rating_type
    AND rs.rating_date = lrs.max_date
-- Medalist Rating
LEFT JOIN latest_rating lrmedal ON lrmedal.fund_id = f.fund_id AND lrmedal.rating_type = 'Medalist Rating'
LEFT JOIN fund_rating rmedal
    ON rmedal.fund_id = lrmedal.fund_id
    AND rmedal.rating_type = lrmedal.rating_type
    AND rmedal.rating_date = lrmedal.max_date
-- Sustainability Rating
LEFT JOIN latest_rating lresg ON lresg.fund_id = f.fund_id AND lresg.rating_type = 'Sustainability Rating'
LEFT JOIN fund_rating resg
    ON resg.fund_id = lresg.fund_id
    AND resg.rating_type = lresg.rating_type
    AND resg.rating_date = lresg.max_date
-- 主分类 5 个维度
LEFT JOIN primary_category cat_cat       ON cat_cat.fund_id = f.fund_id       AND cat_cat.dimension = 'morningstar_category'
LEFT JOIN primary_category cat_style     ON cat_style.fund_id = f.fund_id     AND cat_style.dimension = 'style_box'
LEFT JOIN primary_category cat_retail    ON cat_retail.fund_id = f.fund_id    AND cat_retail.dimension = 'is_retail_eligible'
LEFT JOIN primary_category cat_index     ON cat_index.fund_id = f.fund_id     AND cat_index.dimension = 'is_index_fund'
LEFT JOIN primary_category cat_leverage  ON cat_leverage.fund_id = f.fund_id  AND cat_leverage.dimension = 'is_leveraged';

CREATE VIEW v_holdings_latest AS
    SELECT h.* FROM fund_holdings_snapshot h
    JOIN (SELECT fund_id, MAX(as_of_date) maxd FROM fund_holdings_snapshot GROUP BY fund_id) m
      ON h.fund_id=m.fund_id AND h.as_of_date=m.maxd
    WHERE COALESCE(h.weight_quarantine,0)=0;

-- ── Unique Indexes (1) ──

CREATE UNIQUE INDEX ux_fund_mid
                   ON fund(morningstar_id) WHERE morningstar_id IS NOT NULL;
