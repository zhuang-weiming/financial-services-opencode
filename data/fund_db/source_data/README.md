# ⚠️ source_data/ — 历史源数据（只读参考，禁止直接入库）

> 本目录由 `phase_1_data/` 更名而来（2026-08-23）。Phase 1 = 项目的初始版本阶段。

## 内容与风险标注

| 路径 | 内容 | ⚠️ 风险声明 |
|---|---|---|
| `screener_us100m/fc_need_to_pull.txt` | 400 个 FC mid 清单 | **🔴 已知污染源**：其中含 400 只被误标 FC 的开放式基金（American Funds 系）。DB 已清理（见 schema §7 #7），**严禁**据此文件重建 FC 池 |
| `screener_us100m/FE_page*.json` (19) / `FO_page*.json` (35) | Morningstar screener 原始分页快照 | 含 FC/FO 双标签原始记录，仅作取证用途 |
| `screener_us100m/*_need_to_pull.txt` `*_missing_data.txt` 等 | Phase 1 的任务清单/进度文件 | 已完成历史使命 |
| `fund_universe_1000_merged.csv` | 早期 universe 合并表 | 被 DB `fund_screener_us100m` 表取代 |
| `lookup_results/` `lookup_backfill_report.md` | ID lookup QA 记录 | 仅存档 |

## 权威来源声明

**当前唯一权威的 screener 池 = `../fund_db.sqlite` 中的三张表**
（`fund_screener_us100m/eu100m/cn_hk100m`，均已带 `passed_filter` 标记）。
池的重建请走 `../pipeline/s1_build_universe.py`，不要从本目录任何文件出发。
