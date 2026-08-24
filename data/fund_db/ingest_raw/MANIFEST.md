# ingest_raw/ — 原始数据归档（按采集日期标注）

> 2026-08-23 重构：原 `ingest_raw_legacy/` 有意义数据并入本目录，空目录与过时快照已删除。
> **红字警告**：Phase-1 批次中的规模字段为 Morningstar `OF009`（**本币口径**），严禁当作 USD 使用；
> 美元权威口径 = `OF99A`，仅存在于 `20260823_phase2_mcp_pulled/size_usd_pull.json` 与 DB `fund.size_usd` 列。

| 目录 | 采集日期 | 来源 | 内容 | 状态 |
|---|---|---|---|---|
| `20260820-22_phase1_mcp_batches/` | 08-20 ~ 08-22 | MCP(旧客户端) | ≈284 个批次 JSON：早期混合批次 + batchFE_D01-69 + batchFC_D01-08，覆盖最初 4,438 只基金 | 归档只读 |
| `20260821-22_phase1_holdings_batches/` | 08-21 ~ 08-22 | fund-holdings-tool | 252 个持仓批次（原始 786 只基金 Top-N） | 归档只读 |
| `20260823_phase2_mcp_pulled/` | 08-23 | MCP(JSON-RPC 新客户端) | 见下分项表 | 归档只读 |

## 20260823_phase2_mcp_pulled/ 分项

| 文件 | 内容 | 规模 |
|---|---|---|
| `fc_remaining_data.json` | FC 补拉（14 datapoint, 含 OS00F） | 130 只 |
| `fo_remaining_data.json` | FO 主批次 | 14,280 只 |
| `eu_screener_results.json` / `eu_fund_data.json` | 卢森堡池 + 全量数据 | 池1000 / 数据990 |
| `cn_hk_screener_results.json` / `cn_hk_fund_data.json` | 中国大陆池 + 全量数据 | 966 只入库 |
| `hk_screener_results.json` / `hk_fund_data.json` | 香港腿（修复#4 后补搜） | 1,300 只全部入库 |
| `us_holdings.json` / `eu_cn_hk_holdings.json` / `us_holdings_more.json` | Top-10 持仓三轮拉取 | 最终合并覆盖 US 18,481 只 |
| `size_usd_pull.json` | **OF99A+OF010+LS05M**（修复 #1/#3/#5 的权威数据源） | 20,521 只 |

## 新拉取落位规则

pipeline 的 s2/s3 会把新批次写入 `phase2_current/YYYYMMDD_*/` 子目录（由 `config.dated_raw_subdir` 自动建目录），请勿手工放置。
