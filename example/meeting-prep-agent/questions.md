# Meeting-Prep-Agent Agent — Example Questions

> **Routing trigger keywords:** client review, client meeting, meeting prep, briefing pack, quarterly review, investment proposal

**Data Files:**
- `data/company_data.csv` — Company trading data
- `data/meeting_brief.json` — Meeting brief

---

## Question 1: Q1 Earnings Review Meeting
```
Prepare for Apple Q1 FY24 earnings review with Meridian Family Office.

Reference: data/company_data.csv (row 1), data/meeting_brief.json

From data/company_data.csv:
- AAPL Q0 Revenue: $119.6B, Q1 Revenue: $121.0B
- Price: $185, Market Cap: $2.9T

From data/meeting_brief.json:
- Meeting Date: 2024-04-15
- Type: Q1 FY24 Earnings Review
- Client: Meridian Family Office

Please:
1) Build company background summary
2) Analyze Q1 performance vs expectations
3) Prepare key questions to ask IR
4) Draft talking points
```

## Question 2: Earnings Preview Setup
```
Set up pre-earnings analysis for AAPL Q2.

Reference: data/company_data.csv

From data/company_data.csv:
- AAPL: Revenue Q0 $119.6B, Q1 $121.0B
- Market Cap: $2.9T

Please:
1) Build estimate model for Q2
2) Identify key metrics to watch
3) Set up bull/bear scenarios
4) Prepare questions for management
```

## Question 3: Build a briefing pack for LP advisory
```
Build a briefing pack for the upcoming LP advisory board meeting.

Reference: data/meeting_brief.json

Please:
1) Summarize fund performance for the period
2) Highlight top/bottom holdings
3) Outline key developments since last meeting
4) Prepare Q&A on portfolio outlook
```

## Question 4: Premier 投后回顾会议全套材料
```
请为即将到来的 Premier 客户投后回顾会议准备全套材料。

Reference: data/premier_review_data.json, data/meeting_brief.json

From data/premier_review_data.json:
- 组合当前价值：$8.9M，YTD +6.8%（超基准 0.6%）
- 持仓从年初至今有显著分化（茅台 +18%，招商银行 -3.5%）
- 另类资产超配 4%，现金比例较高 8%
- 客户新继承 $500K，对 ESG 有兴趣

From data/meeting_brief.json:
- 历史会议格式参考

Please:
1) 准备一份组合表现归因总结（超额收益来源分解）
2) 分析当前配置与目标配置的偏差，标注需要关注的漂移
3) 对每个超配/低配的资产类别提出调仓建议
4) 处理客户新信息和需求（继承 $500K/ESG 兴趣/教育金需求）
5) 起草一个 10 分钟的会议议程
6) 准备一组可能被问到的问题及其回答要点
7) 列出会后跟进事项和责任人
```

## Question 5: Premium 新产品引入评估
```
客户想了解我们推荐的一个新投资策略，请准备对比分析材料。

Reference: data/premier_review_data.json

假设客户感兴趣的产品（演示用）：
- 产品：某全球多资产收益策略基金（股 40% + 债 40% + 另类 20%）
- 近 3 年年化：+9.2%，最大回撤 -12.5%
- 管理费：0.85%
- 与客户当前组合的相关性：0.65

与客户当前组合（从 data/premier_review_data.json 获取）对比：
- 当前 YTD：+6.8%，3 年年化约 +10.5%
- 当前组合最大回撤约 -18%

Please:
1) 对比新策略与客户现有组合的风险收益特征
2) 分析加入该策略后的组合优化效果（有效前沿变化）
3) 评估费用是否合理
4) 建议如果引入该策略，应该替代现有组合中的哪部分配置
5) 给出引入建议：推荐/不推荐/有条件推荐
6) 如果推荐，建议配置比例
```
