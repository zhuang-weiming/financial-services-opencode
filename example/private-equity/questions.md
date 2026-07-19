# Private-Equity Agent — Example Questions

> **Routing trigger keywords:** IC memo, deal screen, deal sourcing, DD checklist, due diligence, buyer list, returns analysis, unit economics, value creation plan

**Data Files:**
- `data/portfolio_performance.csv` — Portfolio performance data
- `data/ic_memo.json` — IC memo for CloudSoft

---

## Question 1: IC Memo Review
```
Review CloudSoft IC memo for investment committee.

Reference: data/ic_memo.json, data/portfolio_performance.csv

From data/ic_memo.json:
- Deal: CloudSoft, $420M EV at 8.2x revenue
- Revenue: $51.2M, Growth 50%, EBITDA margin 16%
- Returns Target: IRR 25%, MOIC 3.0x

From data/portfolio_performance.csv:
- CloudSoft: IRR 35%, MOIC 2.8x (existing investment)
- TechCo: IRR 28%, MOIC 3.1x

Please:
1) Verify financial projections
2) Challenge return assumptions
3) Assess risk factors
4) Make investment recommendation
```

## Question 2: Portfolio Returns Analysis
```
Analyze portfolio performance across holdings.

Reference: data/portfolio_performance.csv

From data/portfolio_performance.csv:
- TechCo: 10.2x entry, 14.5x exit, 28% IRR, 3.1x MOIC
- CloudSoft: 8.5x entry, 12.0x exit, 35% IRR, 2.8x MOIC
- DataFlow: 6.0x entry, 8.5x exit, 18% IRR, 2.2x MOIC

Please:
1) Build IRR waterfall
2) Calculate weighted avg returns
3) Identify underperformers
4) Recommend portfolio actions
```

## Question 3: Screen inbound deals from this week
```
Screen inbound deals from this week's batch against our investment thesis.

Reference: data/ic_memo.json

Please:
1) Extract key deal metrics from each opportunity
2) Run pass/fail against our fund criteria
3) Flag any that merit a first call
4) Output a one-page screening memo for each
```

## Question 4: Premier 私募股权跟投机会评估
```
我收到一份 PE 基金的跟投邀请，请帮我全面评估这个投资机会。

Reference: data/premier_coinvest_opportunity.json, data/ic_memo.json

From data/premier_coinvest_opportunity.json:
- 目标公司 DataInfra：SaaS 企业，营收 1850 万，增长 42%，NRR 125%
- 投资额：500 万，占 4%，投前估值 1.2 亿
- 回报预测：基础 IRR 22.5%/MOIC 2.8x
- 与 HHH Technology Fund III 共同投资

From data/ic_memo.json:
- CloudSoft IC memo 作为同类 IC 审查参考框架

Please:
1) 评估目标公司的业务质量（增长/GM/NRR/单位经济模型）
2) 分析估值是否合理（对比 SaaS 同业 EV/Revenue 倍数）
3) 审查交易条款（清算优先/反稀释/信息权）
4) 对回报预测做敏感性分析（退出倍数 × 增长率矩阵）
5) 评估基金本身的质量（管理团队/历史业绩/利益一致性）
6) 分析跟投与主基金的潜在利益冲突
7) 给出最终建议：投/不投，以及最大投资额建议
8) 如果值得投，建议这笔跟投在我的总资产中占比多少
```

## Question 5: Premier 的另类资产配置策略
```
我在考虑将一部分资金配置到另类资产（PE/私募债/REITs/实物资产），请帮我制定策略。

Reference: data/premier_coinvest_opportunity.json

假设我的总可投资资产为 2000 万元，目前全部在传统股债组合中。

From data/premier_coinvest_opportunity.json:
- PE 跟投门槛 500 万起
- 退出周期 5-7 年
- 流动性差

Please:
1) 根据我的资产规模（2000 万），建议另类投资的合理比例（10-20%？）
2) 构建另类投资子组合（PE/私募债/REITs/商品/基础设施各多少）
3) 流动性分层管理：将资产按 1/3/5/10 年流动性需求分层
4) 分析另类投资的 J-curve 效应（前几年账面回报为负）
5) 给出节奏建议：多少时间内逐步建仓完毕
6) 替代方案：如果不想做 PE 跟投，有哪些流动性更好的替代（如私募 REITs/私募债基金/实物资产 ETF）
```
