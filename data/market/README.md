# data/market/ — 市场行情时序数据

> **用途:** A 股 / 美股 / 港股 / 大宗 / 利率的日频数据，append-only 时序
> **格式:** CSV（结构化，便于回测 + 因子计算）
> **更新频率:** 每个交易日 EOD 收市后
> **来源:** 原始数据源（Eastmoney / Tencent / Sina / yfinance / CNBC / FRED）

---

## Schema

### `daily_indices_YYYY.csv` — 指数日线

```csv
date,ticker,name,close,change_pct,volume,source,notes
2026-07-29,000300,CSI300,4519.50,+0.67,,Tencent,
2026-07-29,SPY,S&P500 ETF,730.42,-1.54,,Morningstar-MCP,
2026-07-30,000300,CSI300,4549.72,+0.67,,Tencent,
```

**字段说明：**

| 字段 | 类型 | 单位 | 说明 |
|:-----|:-----|:-----|:-----|
| `date` | ISO date | — | YYYY-MM-DD |
| `ticker` | string | — | 内部 ticker（沪深用 6 位代码，美股用交易所代码）|
| `name` | string | — | 中文/英文名 |
| `close` | float | 本币 | 收盘价（指数点位或 ETF 价格）|
| `change_pct` | float | % | 当日涨跌幅（含正负号）|
| `volume` | float | 取决于标的 | 成交额/成交量（指数无量）|
| `source` | string | — | 数据源（Tencent/Eastmoney/yfinance/CNBC/Morningstar-MCP）|
| `notes` | string | — | 备注（如有重大事件）|

### `daily_macro_YYYY.csv` — 宏观指标日线

```csv
date,indicator,value,unit,source,notes
2026-07-29,US30Y,5.207,%,CNBC,首次突破 5.20% 自 2007
2026-07-30,US30Y,5.184,%,CNBC,盘中 5.218% 后回落
2026-07-29,Brent,93.00,USD/bbl,Morningstar-MCP,USO +7.32% 同日
2026-07-30,Brent,88.16,USD/bbl,Morningstar-MCP,Hormuz 交通恢复
```

**字段说明：**

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| `date` | ISO date | YYYY-MM-DD |
| `indicator` | string | US30Y/US10Y/US2Y/Brent/WTI/USO/DXY/VIX 等 |
| `value` | float | 数值 |
| `unit` | string | %/USD-bbl/USD-index/points 等 |
| `source` | string | 数据源 |
| `notes` | string | 关键事件或异常 |

### `us_debt_gdp_history_1790_2026.csv` — 美债 250 年轨迹（静态历史锚点）

```csv
year,debt_gdp_pct,trigger_event,source,notes
1946,119,WWII 结束（与今天相当）,user-provided,历史峰值 119-121%；本文献基准案例起点
1974,35,28 年下降后低点,user-provided,1946-74 金融抑制期终点；r<g 持续 28 年
2026,120,当前,framework,HYP-003/US_EQUITY_FRAMEWORK 当前值
```

**字段说明：**

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| `year` | int | 年份（低频，非日频）|
| `debt_gdp_pct` | float | 债务/GDP % |
| `trigger_event` | string | 触发事件（战争/政策/危机）|
| `source` | string | user-provided / framework / MCP / 文献 |
| `notes` | string | 口径修订、交叉参考、关键含义 |

### `us_debt_2026_diagnostics.csv` — 2026 美债可持续性诊断快照

```csv
metric,value,unit,threshold,meaning,source,notes
us_5y_cds,38,bp,100 / 200,健康 / 危机,Investing.com USGV5YUSAB=R,HYP-011 S1
us30y,5.184,%,5.0 / 7.0,重定价 / 失控,HYP-017,快速剧本失控线 7%+
```

**字段说明：**

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| `metric` | string | 指标名（debt_gdp_ratio / primary_deficit / us_5y_cds / us30y 等）|
| `value` | string | 当前值（区间用 a-b）|
| `unit` | string | % / bp / index / x |
| `threshold` | string | 触发阈值（可多级，用 / 分隔）|
| `meaning` | string | 阈值含义 |
| `source` | string | 数据源 |
| `notes` | string | 关联 HYP / 框架条目 |

---

## 命名约定

| 数据类型 | 文件名 | 例子 |
|:---------|:-------|:-----|
| 指数日线 | `daily_indices_YYYY.csv` | `daily_indices_2026.csv` |
| 宏观日线 | `daily_macro_YYYY.csv` | `daily_macro_2026.csv` |
| 个股日线 | `daily_<ticker>_YYYY.csv` | `daily_601788_2026.csv`（光大证券）|
| 历史锚点（低频静态）| `us_debt_gdp_history_*.csv` | `us_debt_gdp_history_1790_2026.csv` |
| 诊断快照（静态）| `us_debt_2026_diagnostics.csv` | `us_debt_2026_diagnostics.csv` |

**A 股 ticker 命名：** 6 位代码前补 0 至 6 位（600519 = 贵州茅台）
**美股 ticker 命名：** 用交易所代码（MSFT/NVDA/SPY/QQQ）

### `daily/<code>_<name>.csv` — 个股/ETF OHLCV（集中化，跨 subagent 共享）

```csv
date,code,open,close,high,low,volume
2026-08-10,000001,11.18,11.29,11.38,11.16,88906014
```

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| `date` | ISO date | 交易日 |
| `code` | string | 6 位代码 |
| `open/close/high/low` | float | 价格（前复权 as-is） |
| `volume` | int | 成交量（股） |

**细节：**
- 统一命名 `<code>_<name>.csv`（如 `000001_平安银行.csv`），全量清单见 `daily/INDEX.md`
- 来源: Sina API（`data_loader.py` 自动下载 + 永久落盘）
- 加载: 用 `.opencode/memory/personal-system/sell-ladder/data_loader.py` 的 `load_daily(ticker)`（搜索本目录 → fallback → Sina），不直接 read_csv
- 已有 89 个 A 股/ETF 标的（历史上散落在 sell-ladder/data/ 的已迁移至此）

---

## 写入规则

1. **append-only** —— 新交易日 append 新行，**不修改**历史
2. **同一天可有多行**（如一个指数 7-30 同时有 close 和 intraday_high，notes 区分）
3. **缺数据写 null** —— 不要用 0 或估算值填充
4. **每次写入**在 raw-log 留一行说明（哪个 subagent、为什么）

---

## 数据完整性

- ✅ **真实数据**：从 MCP / 数据源直接获取
- ⚠️ **估算数据**：写 [ESTIMATED] 在 notes 字段
- ❌ **缺失数据**：不写入，下一次 fetch 时补

---

## 与 raw-log/ 的关系

| raw-log/ | data/market/ |
|:---------|:-------------|
| 叙事 + 解读（Markdown）| 结构化数据（CSV）|
| 一次性事件记录 | 时序累计 |
| grep 关键词 | 按 ticker/date 查询 |
| 复盘思考用 | 跨 subagent 共享 |