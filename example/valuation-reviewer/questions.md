# Valuation-Reviewer Agent — Example Questions

> **Routing trigger keywords:** valuation review, returns analysis, portfolio monitoring, IC memo review, LP reporting, GP package, stress-test valuation

**Data Files:**
- `data/valuation_data.csv` — Valuation comps
- `data/valuation_review.json` — Detailed valuation review

---

## Question 1: DCF Valuation Review
```
Challenge the Datadog DCF valuation.

Reference: data/valuation_data.csv, data/valuation_review.json

From data/valuation_data.csv:
- Datadog: Price $118, Target $140, Upside 18.6%
- WACC: 10.5%, Terminal Growth: 4.5%

From data/valuation_review.json:
- Base Case DCF: $140
- Bear Case: $115, Bull Case: $168
- Flags: Terminal growth upper range, margin assumption aggressive

Please:
1) Stress-test WACC assumptions
2) Challenge terminal growth rate
3) Test margin expansion sensitivity
4) Assess if current price reflects risk
```

## Question 2: Cloud Comp Set Valuation
```
Compare valuations across cloud infrastructure comps.

Reference: data/valuation_data.csv

From data/valuation_data.csv:
- Datadog: Upside 18.6%, WACC 10.5%
- Snowflake: Upside 25.7%, WACC 10.8%
- MongoDB: Upside 32.0%, WACC 11.2%

Please:
1) Normalize for growth differences
2) Rank by risk-adjusted upside
3) Identify best risk/reward
4) Draft allocation recommendation
```

## Question 3: Stress-test the DCF model with WACC adjustment
```
Stress-test the DCF model with a -100bps WACC adjustment to see valuation impact.

Reference: data/valuation_data.csv, data/valuation_review.json

Please:
1) Recalculate DCF value with lower WACC
2) Show sensitivity table (WACC ± 200bps × terminal growth ± 1%)
3) Identify which assumption has the highest leverage
4) Flag if the base case is too aggressive
```

## Question 4: Premier 持仓估值合理性检查
```
请对我持仓中的主要股票进行估值合理性检查。

Reference: data/premier_valuation_check.csv

From data/premier_valuation_check.csv:
- 6 只主要持仓的估值指标（PE/PB/EV-EBITDA/PEG）
- 当前价 vs 分析师目标价
- 历史平均估值对比
- 做空比例和内部人持股

Please:
1) 对每只持仓做当前估值 vs 历史均值的对比
2) 用 PEG 指标判断估值与增长的匹配度（PEG < 1 低估，> 2 高估）
3) 与同行业公司做横向估值对比
4) 做空比例高的股票（AMZN 1.5%）—— 这是一个反向指标还是警示信号？
5) 内部人持股——长江电力 55% 是好事（利益一致）还是坏事（流动性差）？
6) 按估值合理性程度排序（从最合理到最不合理）
7) 对排名靠后的股票，给出调仓建议和替代标的
8) 整体组合的估值水平是否在合理范围？存在系统性高估吗？
```

## Question 5: 新资金配置的压力测试分析
```
我有一笔 500 万元的新资金需要配置，请帮我做配置方案和压力测试。

Reference: data/premier_new_money.json, data/premier_valuation_check.csv

From data/premier_new_money.json:
- 新资金：500 万
- 当前已有组合：890 万
- 投资期限 10-15 年，中等风险
- ESG 偏好，排除烟草/武器
- 1 年内流动性需求：15 万，3 年 60 万，5 年+ 100 万

From data/premier_valuation_check.csv:
- 当前持仓估值状态参考

Please:
1) 设计 500 万新资金配置方案（含具体 ETF/股票配比）
2) 结合现有组合，计算合并后的总资产配置
3) 做 3 个压力测试情景：
   - 情景 A：美股暴跌 30%（类似 2022）
   - 情景 B：A股持续低迷（类似 2023-2024）
   - 情景 C：通胀反弹，股债双杀
4) 在各压力情景下估算组合最大回撤和恢复时间
5) 确保配置方案满足流动性需求（资金何时需要可用）
6) 给出推荐的建仓节奏（一次性 vs 分批建仓）
```
