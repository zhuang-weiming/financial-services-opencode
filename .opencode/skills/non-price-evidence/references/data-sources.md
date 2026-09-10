# 非价格数据源地图（完整矩阵）

> 数据截止 2026-09-10 实测。状态：✅ 可用 · ⚠️ 间歇/受限 · ❌ 不可用 · 💰 付费

## 1. 成交量结构

| 粒度 | 工具 / 源 | 市场 | 认证 | 实测 |
|---|---|---|---|---|
| 日线 OHLCV | 腾讯 `web.ifzq.gtimg.cn`（自建）| A/港/美 | 无 | ✅ |
| 日线 OHLCV | `get_market_data`（vibe-trading）| 全市场 | 无 | ❌ MCP 超时 |
| 日线 OHLCV | 东财 `push2` | A/港/美 | 无 | ✅ |
| 分钟线 1m-60m | `vibe-trading-minute-analysis` | A股 | 无 | ⚠️ 未验证 |
| 1h 日内 | `llmquant-data_equity_intraday_prices` | 美股（14d）| API key | ⚠️ 额度 |
| 1m 日内 | yfinance | 美股（7d）| 无 | ⚠️ IP 限速 |
| 分笔/逐笔 | tushare pro | A股 | 积分 | 💰 |
| 分笔 | mootdx | A股 | 无 | ⚠️ |
| 逐笔/Orderbook L2 | `orderbook_depth` MCP | Crypto | 无 | ❌ 超时 |
| Level2 十档 | QVeris / 券商 API | A股 | 付费 | 💰 |
| 换手率 | 东财 `push2` f168 | A股 | 无 | ⚠️ 未接入 |
| 量价指标 | 自算（OBV/AD/量比）| 全市场 | 无 | ✅ |

## 2. 资金流向

### A股（东财，免鉴权）
| 数据 | 端点 / 工具 | 实测 |
|---|---|---|
| 主力/超大单/大单/中单/小单净流入 | `get_fund_flow`（push2his）| ❌ 直连被限，用 MCP |
| 龙虎榜 | RPT_DAILYBILLBOARD_DETAILSNEW | ✅ |
| 两融 | RPTA_WEB_RZRQ_GGMX | ✅ |
| 大宗交易 | RPT_DATA_BLOCKTRADE | ✅ |
| 股东户数 | RPT_HOLDERNUMLATEST | ✅ |
| 限售解禁 | RPT_LIFT_STAGE | ✅ |
| 北向持股 | RPT_MUTUAL_HOLDSTOCKNORTH_STA | ✅ |
| 北向资金流 | `get_northbound_flow` | ⚠️ |
| 十大流通股东 | 季报 | 季度 |

### 美股
| 数据 | 工具 | 认证 | 实测 |
|---|---|---|---|
| 机构持仓 13F | `llmquant-data_sec_13f_*` | API key | ✅ 0 credits |
| 内部人 Form 4 | `vibe-trading-sec-edgar` | 无 | ✅ |
| 基金持股 | `morningstar-security-ownership-tool` | MCP | ✅ |
| 主力净流入 | `get_fund_flow` | 无 | ⚠️ |

### Crypto
| 数据 | 工具 |
|---|---|
| 清算热图 | `vibe-trading-liquidation-heatmap` |
| 稳定币流 | `vibe-trading-stablecoin-flow` |
| 链上分析 | `vibe-trading-onchain-analysis` |
| Funding / OI | OKX API / `vibe-trading-perp-funding-basis` |

## 3. 基本面

### A股 / 港股
| 数据 | 工具 | 实测 |
|---|---|---|
| 财务指标 | 东财 RPT_LICO_FN_CPD | ✅ |
| 一致预期 EPS/PE | 东财 RPT_WEB_RESPREDICT | ✅ |
| 三大报表 | `get_financial_statements` | ✅ |
| 券商研报 | `get_research_reports` | ✅ |
| 基本面筛选 | `vibe-trading-fundamental-filter` | ✅ |

### 美股
| 数据 | 工具 | 认证 | 实测 |
|---|---|---|---|
| 10-K/Q/8-K 文本 | `llmquant-data_sec_filing_read` | API key | ✅ 0 credits |
| XBRL 财务序列 | `get_sec_filings(metric=...)` | 无 | ✅ |
| 估值/预测/持仓 | `get_stock_profile` | 无 | ✅ |
| 分析师报告 | `morningstar-analyst-research-tool` | MCP | ✅ |
| 500+ datapoints | `morningstar-data-tool` | MCP | ✅ |
| 筛选 | `morningstar-screener-tool` | MCP | ✅ |
| 组合 X-Ray | `morningstar-portfolio-analysis-tool` | MCP | ✅ |
| 基金持仓 | `morningstar-fund-holdings-tool` | MCP | ✅ |
| 机构级财务 | FactSet（经 Morningstar gateway）| MCP | ✅ |

## 4. 宏观

| 数据 | 工具 | 认证 | 实测 |
|---|---|---|---|
| 中国 CPI/PPI/M2/社融/GDP | akshare `macro_china_*` | 无 | ✅ |
| 美国宏观（~50 series）| `llmquant-data_macro_*` | API key | ✅ 0 credits |
| FRED 任意 series | `get_macro_series` | `FRED_API_KEY` | ⚠️ |
| 事件隐含概率 | `llmquant-data_polymarket_*` | API key | ✅ |
| 地缘风险 | `vibe-trading-geopolitical-risk` | 无 | ✅ |
| 全球宏观框架 | `vibe-trading-global-macro` / `macro-analysis` | 无 | ✅ |

---

## 已知操作问题（2026-09-10 实测）

| 问题 | 影响 | 绕过 |
|---|---|---|
| `vibe-trading` MCP 全部超时 | get_market_data / fund_flow / … | 腾讯/东财直连 + 自建脚本 |
| 东财 `push2his` IP 限 | 资金流（主力净流入）| MCP `get_fund_flow` 或等待 |
| `llmquant-data` credits 耗尽 | news / etf_holdings | 充值；macro/13F/SEC 仍 0 credits |
| FRED 直连超时 | 美国宏观 | MCP `llmquant-data_macro_*` |
| akshare 东财系接口间歇 | 部分行情 | 腾讯直连 |

## 数据新鲜度参考

| 数据 | 更新频率 | 典型滞后 |
|---|---|---|
| 日线 OHLCV | 每日 | T+0 盘后 |
| 两融 | 每日 | T+1 |
| 北向持股 | 每日（2024-08 后改为季度披露）| 季度 |
| 股东户数 | 季报 | 1 季度 |
| 大宗交易 | 每日 | T+1 |
| 财务指标 | 季报 | 1-2 月 |
| 一致预期 | 不定期 | 周-月 |
| 中国宏观 | 月度 | 1-2 周 |
| 美国宏观 | 月度/季度 | 1-4 周 |
| 13F | 季度 | 45 天 |
| SEC filing | 事件驱动 | 即时 |
