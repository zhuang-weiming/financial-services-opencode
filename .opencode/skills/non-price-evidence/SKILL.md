---
name: non-price-evidence
description: 非价格证据层 (4 维度)。当需要为趋势/估值结论做**独立验证**（超越价格类算法的"伪共识"）时加载。四维 = 成交量结构(换手/量比/OBV/AD/量价分布) + 资金流向(A股两融/股东户数/龙虎榜/大宗/解禁/北向 + 美股13F/Form4 + Crypto链上) + 基本面(财务指标/一致预期/三大报表/SEC文本/Morningstar) + 宏观(中国CPI/PPI/M2/社融 + FRED/Polymarket)。与 trend-analysis-multi-algo 的 10 个价格算法交叉验证，解决"同一价格序列的多种变换被误认为独立证据"的问题。
category: data-source
---

# 非价格证据层 (non-price-evidence)

## 为什么需要这一层

`trend-analysis-multi-algo` 的 10 个算法**全部读同一 OHLCV 序列** —— 它们的"共识"是同一数据的多种变换，**不是独立证据**（该协议自己的 Why 5 已披露此局限）。

本 skill 提供**真正独立**的 4 个维度。价格算法 + 非价格证据 = 完整的验证结构。

## 快速使用

```bash
# 四维全采
python3 scripts/fetch_evidence.py --code 601788 --market sh

# 仅成交量 + 资金流
python3 scripts/fetch_evidence.py --code 600519 --market sh --dimensions volume,fund

# 输出 JSON (供 agent 合成)
python3 scripts/fetch_evidence.py --code 601788 --market sh --json-out /tmp/ev.json
```

## 四维矩阵

### 维度 1 — 成交量结构（脚本内，腾讯 OHLCV 计算）

| 读数 | 含义 |
|---|---|
| `volume_ratio_20_60` | 20 日/60 日均量比（>1.1 放量 / <0.9 缩量）|
| `volume_trend` | 放量 / 缩量 / 平量 |
| `obv_20d_slope` | OBV 20 日斜率 |
| `obv_price_divergence` | 量价同向 / 背离 ⚠️ |
| `ad_line_20d_slope` | AD Line（腾落线）斜率 |
| `updown_volume_ratio` | 上涨日/下跌日成交量比 |
| `vol_60d_annualized` | 60 日年化波动率 |
| `price_vs_ma20` | 价格距 MA20 百分比 |

**缺口**：逐笔/Level2 十档（付费）；换手率（需流通股本）。

### 维度 2 — 资金流向

**脚本内（东财 datacenter，免鉴权）**：
| 读数 | 源 |
|---|---|
| `margin_balance_yi` / `margin_5d_change_yi` | 两融（RPTA_WEB_RZRQ_GGMX）|
| `holder_count` / `holder_count_chg_pct` | 股东户数（RPT_HOLDERNUMLATEST）|
| `dragon_tiger_events` | 龙虎榜（RPT_DAILYBILLBOARD_DETAILSNEW）|
| `block_trades` | 大宗交易（RPT_DATA_BLOCKTRADE）|
| `lockup_upcoming` | 限售解禁（RPT_LIFT_STAGE）|
| `northbound_hold_ratio` | 北向持股（RPT_MUTUAL_HOLDSTOCKNORTH_STA）|

**需 MCP（agent 调用）**：
| 数据 | 工具 |
|---|---|
| A股主力/超大单净流入 | `get_fund_flow`（push2his 被 IP 限时用此）|
| 美股机构持仓 | `llmquant-data_sec_13f_list_ticker_holders` ✅ 0 credits |
| 美股内部人交易 | `vibe-trading-sec-edgar`（Form 4）|
| 基金持股分布 | `morningstar-security-ownership-tool` |
| Crypto 清算热图/稳定币流/链上 | `vibe-trading-liquidation-heatmap` / `stablecoin-flow` / `onchain-analysis` |

### 维度 3 — 基本面

**脚本内（东财 datacenter）**：
| 读数 | 源 |
|---|---|
| `latest_report`（营收/净利/ROE/EPS/BPS）| 财务指标（RPT_LICO_FN_CPD）|
| `netprofit_yoy_pct` | 净利润同比 |
| `consensus`（EPS/PE 预测）| 一致预期（RPT_WEB_RESPREDICT）|

**需 MCP（agent 调用）**：
| 数据 | 工具 |
|---|---|
| 三大报表全文 | `get_financial_statements`（A/港/美）|
| SEC 10-K/Q/8-K 文本（MD&A/风险因素/earnings release）| `llmquant-data_sec_filing_read` ✅ 0 credits |
| XBRL 财务序列 | `get_sec_filings(metric=...)` |
| 分析师报告 / 公允价值 / 护城河 / 500+ datapoints | **Morningstar MCP** |
| 机构级财务 | FactSet（经 Morningstar gateway）|

### 维度 4 — 宏观

**脚本内（akshare）**：
| 读数 | 源 |
|---|---|
| `china_cpi_yoy` | CPI 年率（2026-08 = 0.8%）|
| `china_ppi_yoy` | PPI 年率（2026-08 = 3.8%）|
| `china_m2_yoy` | M2 同比（2026-07 = 7.7%）|
| `china_shrzgm` | 社融增量 |
| `china_gdp_yoy` | GDP 年率 |
| `hyp029_trigger_status` | **HYP-029 中国反向操作 5 项触发监控**（CPI≥2% / PPI转正 / M2>9%）|

**需 MCP（agent 调用）**：
| 数据 | 工具 |
|---|---|
| 美国宏观（CPI/Fed Funds/NFCI/PCE/收益率曲线）| `llmquant-data_macro_*` ✅ 0 credits |
| FRED 任意 series | `get_macro_series`（需 `FRED_API_KEY`）|
| 事件隐含概率 | `llmquant-data_polymarket_*` ✅ |
| 地缘风险 | `vibe-trading-geopolitical-risk` |

## 与趋势协议的交叉验证规则

```
价格算法 (trend-analysis-multi-algo, 10 算法)
        ×
非价格证据 (本 skill, 4 维度)
        ↓
┌─────────────────────────────────────────────────┐
│ 价格分歧 + 非价格一致  → 非价格可能是领先信号      │
│ 价格同向 + 非价格同向  → 提高置信度               │
│ 价格同向 + 非价格矛盾  → 标注"未决"，不下结论      │
│ 价格分歧 + 非价格分歧  → 明确"无信号"             │
└─────────────────────────────────────────────────┘
```

**核心原则**：非价格维度是**真正独立**的（不同数据生成过程），价格类算法内部是**伪独立**。因此交叉验证的权重应向非价格倾斜。

## 输出解读

脚本输出含三个关键元数据：
- **`sources`** — 每个数据源的可用状态（✅/⚠️/❌）—— 诚实标注
- **`gaps`** — 未覆盖的数据（需 MCP 或付费源）
- **`stale_flags`** — 陈旧数据（>90 天）—— 防止用过期数据下结论

## 依赖

```bash
pip install pandas numpy requests akshare
# 东财/腾讯/akshare 均免鉴权；MCP 源需 agent 侧调用
```

## 常见陷阱

1. **东财 push2his 被 IP 限** — 资金流（主力净流入）直连常失败 → 用 MCP `get_fund_flow`
2. **akshare 宏观 series 结构不一** — CPI 用 `macro_china_cpi()`（desc，`全国-同比增长`），PPI 用 `macro_china_ppi()`（desc，`当月同比增长`），社融 `macro_china_shrzgm()`（**asc**）—— 已在本脚本内处理
3. **股东户数滞后** — 季报披露，最新通常是上一季度
4. **北向持股为季末快照** — 非实时
5. **MCP 源不在脚本内** — 脚本只覆盖 Python 直连源；MCP 工具必须由 agent 调用
6. **信用额度** — `llmquant-data` 的 `news_browse`/`etf_holdings` 消耗 credits；`macro`/`13F`/`sec_filing` 为 0 credits

## 完整数据源地图

见 `references/data-sources.md` — 四维 × 全市场 × 工具 × 认证 × 实测状态的完整矩阵。
