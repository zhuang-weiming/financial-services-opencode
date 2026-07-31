# data/cache/ — 临时缓存

> **用途:** subagent 任务执行中的中间结果、聚合数据
> **格式:** 任意（CSV / JSON / Parquet，按需）
> **TTL:** 30 天（过期可清理）
> **写入规则:** 任何 subagent 都可以写，但必须注明 task_id 和日期

---

## 写入规则

1. **命名**: `<subagent>_<task>_<date>.<ext>`
   - 例：`alpha-researcher_factor_screen_20260731.csv`
   - 例：`backtest-builder_wt1_decay_20260729.json`
2. **每个文件头部含 metadata**:
   ```json
   {
     "task_id": "...",
     "subagent": "...",
     "created_at": "YYYY-MM-DD",
     "expires_at": "YYYY-MM-DD",
     "source_data": "...",
     "notes": "..."
   }
   ```
3. **可清理** —— 超过 30 天的文件可以删除（不影响主数据）

---

## 与主数据的区别

| `data/cache/` | `data/{market,earnings,factors}/` |
|:--------------|:----------------------------------|
| 临时 | 持续 |
| 中间结果 | 已验证事实 |
| 可清理 | append-only |
| 任务级 | 跨任务共享 |

---

## 清理脚本

每月 1 号自动清理超过 30 天的 cache 文件（避免脚本实现前先人工清理）。