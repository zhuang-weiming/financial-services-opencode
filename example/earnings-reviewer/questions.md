# Earnings-Reviewer Agent — Example Questions

> **Routing trigger keywords:** earnings, post-earnings, quarterly results, Q1/Q2/Q3/Q4, earnings update, quarterly update

**Data Files:**
- `data/earnings_actuals.csv` — Actual earnings results
- `data/earnings_season.json` — Earnings calendar

---

## Question 1: Q1 2024 Earnings Analysis
```
Analyze Q1 2024 earnings results for AAPL and MSFT.

Reference: data/earnings_actuals.csv, data/earnings_season.json

From data/earnings_actuals.csv:
- AAPL: Revenue $119.6B (Beat), EPS $2.18 vs $2.10 est
- MSFT: Revenue $62.0B (Beat), EPS $2.93 vs $2.77 est
- GOOGL: Revenue $76.1B (Miss), EPS $1.64 vs $1.85 est

Please:
1) Summarize beat/miss analysis
2) Highlight key metrics vs expectations
3) Update thesis if needed
4) Draft brief client note
```

## Question 2: Earnings Season Prep
```
Prepare coverage notes for upcoming earnings season.

Reference: data/earnings_season.json

From data/earnings_season.json:
- Season: Q1 2024
- Period: Jan 22 - Feb 15, 2024
- 3 companies reporting

Please:
1) Build estimate model for each
2) Identify key metrics to watch
3) Set up bull/bear scenarios
4) Draft positioning notes
```

## Question 3: Compare Q1 actuals to consensus
```
Compare Q1 2024 actuals to consensus estimates across the coverage list.

Reference: data/earnings_actuals.csv

Please:
1) Calculate surprise percentage for each name
2) Flag positive/negative surprises
3) Identify trend changes from prior quarters
4) Highlight names requiring model updates
```

## Question 4: 财报季持仓优先级排序
```
财报季即将来临，请帮我分析 Premier 持仓中哪些股票最值得重点关注。

Reference: data/premier_earnings_watchlist.json, data/earnings_actuals.csv

From data/premier_earnings_watchlist.json:
- 我的组合中 4 只股票将在未来 2 月内披露财报
- 每只股票我有自己的 EPS 预估，部分与市场共识存在差异

From data/earnings_actuals.csv:
- 参考上季度的实际 vs 预期数据判断管理层披露风格

Please:
1) 按"预期差大小 × 持仓权重 × 历史波动率"排序，确定最值得关注的股票
2) 对排名靠前的每只股票，分析我与市场共识差异的核心原因
3) 针对每只持仓，列出财报中需要特别关注的关键指标（多于 3 个）
4) 为每只股票设定超预期/符合预期/不及预期的情景分析
5) 给出财报后的行动预案：什么情况下加仓/持有/减仓
6) 标注需要关注的外部因素（宏观/行业/竞争）
```

## Question 5: 财报后快速行动方案
```
贵州茅台刚发布了最新季度财报，请帮我快速分析并提供行动建议。

Reference: data/premier_earnings_watchlist.json

假设最新财报数据如下：
- 实际 EPS：79.8（vs 我的预期 80.2，略低于预期 -0.5%）
- 营收增长：+13.5%（vs 预期 +14.0%）
- 净利润率：49.8%（vs 预期 50.0%）
- 全年指引：维持不变
- 分红：中期分红每股 30 元（超预期）

Please:
1) 分析该季度的 beat/miss 情况，判断是质量问题还是噪音
2) 计算财报后合理估值区间（维持/上调/下调目标价）
3) 结合我的持仓成本和仓位比例，给出具体行动建议
4) 如果我要调仓，建议替代标的是什么
5) 列出下次财报前需要关注的关键里程碑
6) 对比我组合中同类持仓的表现，判断是否有相对价值切换机会
```
