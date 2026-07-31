# data/factors/ — 计算后的因子值

> **用途:** 从 earnings/market 派生出的因子值（如 Capex/Revenue 比值、Q/Q 增速、滚动 Z-score 等）
> **格式:** CSV（结构化，便于回测与因子分析）
> **更新频率:** 财报季后立即刷新
> **来源:** 由 subagent 从 `data/earnings/` 计算，不重复存储原始数据

---

## Schema

### `capex_revenue_hyperscalers.csv` — Capex/Cloud Revenue 比值

```csv
ticker,fiscal_period,period_end,ttm_capex_b,cloud_ttm_revenue_b,capex_rev_ratio_pct,status,source
MSFT,FY26,2026-06-30,175.0,100.0,175,HEALTHY,<200-300%>,MSFT Q4 FY26
AMZN,Q1_2026,2026-03-31,147.2,37.6,391,WATCH,<400%+ triggers caution>,AMZN Q1 2026
GOOGL,Q2_2026,2026-06-30,80.0,24.8,323,WATCH,estimated; needs 10-Q exact,GOOGL Q2 2026
META,Q1_2025,2025-03-31,70.0,N/A,N/A,N/A,META Q1 2025
```

### `nvda_qq_growth.csv` — NVDA Q/Q 增速（领先指标）

```csv
quarter,period_end,revenue_b,yoy_pct,qoq_pct,signal,source
Q2_FY25,2024-07-31,N/A,N/A,+16,PEAK,earnings history
Q3_FY25,2024-10-31,N/A,N/A,+17,PEAK,earnings history
Q4_FY25,2025-01-31,N/A,N/A,+12,DECELERATION,earnings history
Q1_FY26,2025-04-30,N/A,N/A,+12,DECELERATION,earnings history
Q2_FY26,2025-07-27,46.74,+56,+6,WATCH (腰斩),NVDA Q2 FY26 earnings
```

---

## 阈值与信号标签

| 指标 | HEALTHY | WATCH | TRIGGER | CONTRADICTED |
|:-----|:--------|:------|:--------|:-------------|
| Capex/Revenue | < 300% | 300-500% | 500%+ (减仓) | n/a |
| NVDA Q/Q | > +10% | +5-10% | < +5% (减仓 50%) | < -20% (清仓) |

---

## 写入规则

1. **append-only** —— 新季度数据点 append 新行
2. **所有原始数据应能在 `data/earnings/` 找到出处** —— 不在 factors 中重复存储
3. **每个因子附阈值定义** —— 用作 trigger / signal
4. **signal 列明确** —— 标记因子当前状态

---

## 与 HYP / BT 的关系

- `data/factors/` 中每个因子通常对应 OPEN_HYPOTHESES.md 中的一条 HYP
- 例：HYP-015 (NVDA Q/Q 领先指标) → `data/factors/nvda_qq_growth.csv`
- 例：HYP-016 (Capex/Revenue 泡沫指标) → `data/factors/capex_revenue_hyperscalers.csv`
- 例：HYP-017 (US30Y 长端) → 用 `data/market/daily_macro_YYYY.csv`，不需要单独 factors 文件