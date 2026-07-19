# Swarm-Orchestrator Agent — Example Questions

> **Routing trigger keywords:** swarm, multi-agent team, investment committee, global equities desk, macro forum, quant strategy desk, multi-perspective analysis

**Data Files:**
- `data/swarm_config.json` — Swarm team configuration and presets
- `data/portfolio_current.json` — Current portfolio holdings for committee review

---

## Question 1: Investment Committee on AAPL
```
Convene an investment committee to analyze AAPL's current investment merits.

Reference: data/swarm_config.json, data/portfolio_current.json

From data/swarm_config.json:
- Available teams: investment_committee, global_equities_desk, macro_strategy_forum, quant_strategy_desk
- Investment committee team members: fundamental analyst, technical analyst, risk officer, sector specialist

Please:
1) Launch the investment_committee swarm team
2) Each member should analyze AAPL from their perspective
3) Synthesize findings into a buy/hold/sell recommendation
4) Highlight areas of agreement and disagreement among members
```

## Question 2: Global Equities Desk on Market Conditions
```
Run the global equities desk team to analyze current market conditions and identify actionable opportunities.

Reference: data/swarm_config.json

Please:
1) Activate the global_equities_desk swarm
2) Have regional specialists cover US, Europe, and Asia
3) Cross-asset analyst reviews fixed income and FX implications
4) Output a consolidated view with top 3 trade ideas
```

## Question 3: Macro Forum on Q3 GDP Outlook
```
Launch the macro strategy forum to debate Q3 GDP outlook and its implications for asset allocation.

Reference: data/swarm_config.json, data/portfolio_current.json

Please:
1) Convene the macro_strategy_forum team
2) Each economist presents their GDP forecast view
3) Debate implications for equities, bonds, and commodities
4) Produce a consensus asset allocation tilt recommendation
```

## Question 4: Premier 投资委员会——500 万新资金配置决策
```
我有一笔 500 万新资金需要配置，请召集投资委员会帮我决策。

Reference: data/premier_new_money.json, data/premier_valuation_check.csv

From data/premier_new_money.json:
- 新资金 500 万，现有组合 890 万
- 投资期限 10-15 年，中等风险
- ESG 偏好，有流动性和集中度限制

From data/premier_valuation_check.csv:
- 当前持仓估值状态

请召集以下角色参与讨论：
1) 宏观分析师：分析当前全球经济周期、利率前景、通胀走势
2) 权益策略分析师：美/港/A 股哪个市场性价比最高
3) 固定收益分析师：债券在当前利率环境下的配置价值
4) 另类投资分析师：REITs/商品/私募债是否值得配置
5) 风险官：整体组合的风险评估和约束条件检查

Please:
1) 每个角色给出独立的分析和建议（各 200-300 字）
2) 讨论环节：标注哪几个角色之间观点存在分歧
3) 综合给出配置方案（各类资产比例 + 具体标的）
4) 标注推荐方案中的主要风险和应对措施
5) 如果委员会委员意见不一，给出多数派和少数派观点
6) 最终决策和下一步行动计划
```

## Question 5: Premier 全球市场晨会简报
```
请组织一个跨市场分析师团队，给我一份今日市场晨会简报。

Reference: data/premier_valuation_check.csv

请模拟以下角色分别汇报今日要点：
1) 美股分析师：昨夜美股收盘情况、关键板块表现、重要个股新闻
2) 中国分析师：A 股/港股今日关注点、政策动态、北向资金
3) 宏观分析师：今日重要经济数据公布、央行动态、地缘政治
4) 大宗商品分析师：原油/黄金/铜的价格走势和关键驱动
5) 外汇分析师：美元/人民币/主要货币对今日展望

Please:
1) 每个角色给出今日市场观点和关键信号（各 100-200 字）
2) 汇总今日需要重点关注的 3-5 个风险事件
3) 给出 3 个今日可能的交易/配置想法
4) 标注需要进一步跟踪的待确认信息
5) 以晨会纪要格式输出（标题/日期/参会人/要点/行动项）
```
