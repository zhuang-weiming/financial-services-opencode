# data/earnings/ — 季度财报快照

> **用途:** 公司季度财报的关键数据点（营收、AI 业务、capex 等）
> **格式:** JSON（结构化，便于回测与因子计算）
> **更新频率:** 财报季后 1-2 周内填入
> **来源:** 公司 IR 公告 / SEC 10-Q / 财经媒体（CNBC、Bloomberg、Morningstar）

---

## Schema

### 单文件结构：`hyperscalers_YYYY.json`

```json
{
  "schema_version": "1.0",
  "last_updated": "2026-07-30",
  "data_points": {
    "MSFT_Q4_FY26": {
      "ticker": "MSFT",
      "fiscal_period": "Q4_FY26",
      "period_end": "2026-06-30",
      "currency": "USD",
      "revenue_b": 90.01,
      "estimate_b": 87.62,
      "beat_pct": 2.7,
      "yoy_growth_pct": null,
      "qoq_growth_pct": null,
      "segment_metrics": {
        "azure_cc_growth_pct": 43.0,
        "azure_estimate_pct": 40.2,
        "fy26_azure_total_b": ">100",
        "ai_arr_b": 13.5,
        "fy26_capex_b": 175,
        "capex_note": "Includes lease reclassification (useful life 15→25y; finance→operating lease)"
      },
      "after_hours_reaction_pct": "+8-9",
      "source": "MSFT Q4 FY26 earnings release + CNBC live blog 2026-07-29",
      "notes": "FY26 capex higher than Q3 estimate of $80B+"
    },
    "META_Q2_2025": {
      "ticker": "META",
      "fiscal_period": "Q2_2025",
      "period_end": "2025-06-30",
      "currency": "USD",
      "revenue_b": 47.52,
      "yoy_growth_pct": 22,
      "capex_b": 17.01,
      "capex_yoy_pct": 100,
      "source": "META Q2 2025 earnings release",
      "notes": ""
    }
  }
}
```

---

## 字段说明

| 字段 | 必填 | 类型 | 说明 |
|:-----|:-----|:-----|:-----|
| `ticker` | ✅ | string | 股票代码 |
| `fiscal_period` | ✅ | string | Q1/Q2/Q3/Q4 + 财年标识（MSFT 用 FY26；其他用自然年）|
| `period_end` | ✅ | ISO date | 财报期末 |
| `currency` | ✅ | string | USD / CNY / HKD 等 |
| `revenue_b` | ✅ | float | 总营收（十亿单位）|
| `estimate_b` | ❌ | float | 分析师预期（如有）|
| `beat_pct` | ❌ | float | beat = (actual-estimate)/estimate × 100 |
| `yoy_growth_pct` | ❌ | float | 同比增速 |
| `qoq_growth_pct` | ❌ | float | 环比增速（尤其重要：HYP-015 NVDA Q/Q 指标）|
| `segment_metrics` | ❌ | object | 分部数据（Cloud/AI/Capex 等）|
| `after_hours_reaction_pct` | ❌ | string | 盘后股价反应 |
| `source` | ✅ | string | 数据源 |
| `notes` | ❌ | string | 关键说明（如会计政策变更、特殊事件）|

---

## 命名约定

| 数据范围 | 文件名 |
|:---------|:-------|
| 4 hyperscaler × 多季度 | `hyperscalers_YYYY.json`（推荐）|
| 单 ticker 跨多年 | `<TICKER>_earnings.json` |
| 行业集合 | `<industry>_<year>.json` |

---

## 写入规则

1. **append-only** —— 新季度数据点 append 到 `data_points` 对象
2. **不修改历史** —— 即使某季度后续被重述（restated），保留原值 + notes 标注
3. **缺数据不写** —— 字段缺失就留空，不要用占位符
4. **关键时间点必录**：每季的 capex、Cloud/AI segment 增速、Q/Q 增速

---

## 跨文件关系

| `data/earnings/` | `data/factors/` |
|:-----------------|:----------------|
| 原始财报数据（事实）| 计算后的因子值（推断）|
| 例：MSFT capex = $175B | 例：Capex/Revenue 比值 = 175% |

因子计算应基于 earnings 中的原始数据，不重复存储。