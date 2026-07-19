# Equity-Research Agent — Example Questions

> **Routing trigger keywords:** earnings analysis, initiating coverage, coverage initiation, morning note, thesis track, catalyst calendar, model update, coverage update

**Data Files:**
- `data/coverage_universe.csv` — Coverage universe with valuation metrics
- `data/research_report.json` — Sample research report

---

## Question 1: Initiating Coverage Analysis
```
Initiate coverage on Datadog (DDOG-US) based on the coverage universe data.

Reference: data/coverage_universe.csv, data/research_report.json

From data/coverage_universe.csv:
- Revenue FY0: $2.1B
- Growth Rate: 45%
- EBITDA Margin: 22%
- WACC: 10.5%
- Terminal Growth: 4.5%

From data/research_report.json:
- Rating: Buy
- Target Price: $140
- Current Price: $118
- Upside: 18.6%

Please:
1) Analyze the business model and growth drivers
2) Build DCF valuation with assumptions
3) Compare to SaaS comps set
4) Make investment recommendation
```

## Question 2: Compare Cloud Infrastructure Plays
```
Compare Snowflake vs Datadog vs Elastic for sector allocation.

Reference: data/coverage_universe.csv

From data/coverage_universe.csv:
- Snowflake: Revenue $3.2B, Growth 50%, WACC 10.8%
- Datadog: Revenue $2.1B, Growth 45%, WACC 10.5%
- Elastic: Revenue $420M, Growth 30%, WACC 10.5%

Please:
1) Normalize metrics for comparison
2) Score relative to growth/quality
3) Recommend sector weighting
4) Identify best-in-class entry point
```

## Question 3: Run a quick comparable analysis
```
Run a quick comparable analysis on the SaaS coverage universe to identify relative value.

Reference: data/coverage_universe.csv

Please:
1) Calculate EV/Revenue and EV/EBITDA multiples
2) Sort by growth-adjusted valuation
3) Flag outliers on either cheap/expensive side
4) Recommend top pick based on risk/reward
```

## Question 4: Premier 持仓股深度覆盖——贵州茅台
```
作为一位持有贵州茅台的 Premier 投资者，请对该股做一次全面的首次覆盖级分析。

Reference: data/premier_stock_data.csv (rows 1-4), data/research_report.json

From data/premier_stock_data.csv:
- 茅台近 4 年营收从 1275 亿增长至 1950 亿
- ROE 稳定在 30-33%，PE 从 35x 压缩至 22x
- 自由现金流充裕，股息率从 1.2% 升至 2.1%

From data/research_report.json:
- 参考格式：买入/卖出/持有评级、目标价、上行空间

Please:
1) 分析茅台的核心护城河（品牌/定价权/渠道/产能）
2) 建立简化 DCF 估值模型（假设 FCF 增长 10%，WACC 9%，终值增长 4%）
3) 与全球奢侈品同行（LVMH/Hermes/Diageo）做估值对比
4) 当前 22x PE 在历史区间什么分位？是否合理？
5) 给出明确的投资建议：买入/持有/减仓，说明条件
6) 标注关键观察指标和危机关联
```

## Question 5: 构建 Premier 持仓催化剂日历
```
请为我的 Premier 投资组合构建未来 3 个月的催化剂日历。

Reference: data/premier_stock_data.csv

From data/premier_stock_data.csv:
- 我的组合主要持有：贵州茅台、苹果等
- 需要跟踪的催化剂类型：财报、股东大会、产品发布、分红除权、监管政策

Please:
1) 列出未来 3 个月（2026 年 7-9 月）每只持仓股的关键事件和时间线
2) 对每个事件标注预期 Impact（高/中/低）和方向性倾向（正面/中性/负面）
3) 标注哪些事件可能触发调仓决策
4) 对即将到来的财报事件，给出预期的市场共识和我的看法
5) 生成一个简洁的日历视图（表格或时间线格式）
6) 标注需要特别关注的事件前准备动作
```
