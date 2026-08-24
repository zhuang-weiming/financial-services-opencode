# Data — 集中化数据仓库

> **设计原则：** 数据放哪里取决于 **大小、共享范围、更新频率**。
> - **小 + 多 subagent 共享 + 高频** → 这里（`data/`）
> - **大 + 单 skill 用 + 静态** → `.opencode/skills/<skill>/data/`（如 WaveTrend HDF5）
> - **临时** → `data/cache/`（30 天 TTL）

---

## 子目录用途

| 子目录 | 内容 | 数据源 | 更新频率 |
|:-------|:-----|:-------|:---------|
| **`market/`** | 日线收盘价、宏观指标 | Tencent / Eastmoney / yfinance | 每日 |
| **`earnings/`** | 季度财报快照（JSON）| 公开财报 / Morningstar MCP | 每季 |
| **`factors/`** | 计算后的因子值（Capex/Rev、Q/Q 增速等）| 由 subagent 计算 | 每季 |
| **`fund_db/`** | 基金数据库设计 + 快照（13 表规范化存储）| Morningstar / FactSet MCP | 日/周/月 视表而定 |
| **`cache/`** | 临时缓存（中间结果、聚合数据）| 各 subagent | 30 天清 |

### `fund_db/` 子说明

不同于其他子目录以"原始数据文件"为主，`fund_db/` 是一个**结构化数据库项目**：

- 顶层为设计规格书（`schema_v1.0.md`）
- 落地后会有 DDL 脚本、参考数据快照、衍生缓存
- 数据源以 Morningstar + FactSet MCP 为主（自动入库率 ≥ 90%）
- 详见 [`fund_db/README.md`](./fund_db/README.md)

---

## 当前文件清单

> **暂无** — `data/` 目录已建立，待 subagent 首次执行任务时按"小数据集中"原则填充。
> 数据增长应 **append-only**，不覆盖历史。

---

## 命名约定

- 日线数据：`daily_<market>_<year>.csv`（如 `daily_csi300_2026.csv`）
- 财报快照：`<ticker>_<quarter>_<fy>.json`（如 `nvda_q2_fy26.json`）
- 因子值：`<factor_name>_history.csv`（如 `capex_revenue_history.csv`）
- 缓存：`<subagent>_<task>_<date}.csv`（如 `alpha-engine-v21_factor_screen_20260731.csv`）

---

## 与 out/ 的区别

| 维度 | `out/` | `data/` |
|:-----|:-------|:-------|
| 内容 | 一次性分析报告 / 输出 | 持续数据 / 时间序列 |
| 生命周期 | 任务结束即过时 | append-only |
| 清理策略 | 月度归档或删除 | 仅 30 天清 cache |
| 跨 subagent | 否 | 是 |