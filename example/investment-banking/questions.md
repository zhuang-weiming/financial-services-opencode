# Investment-Banking Agent — Example Questions

> **Routing trigger keywords:** pitch deck, pitch-deck, CIM, teaser, buyer list, deal tracker, process letter, merger model, datapack, sell-side, M&A, buy-side

**Data Files:**
- `data/precedent_transactions.csv` — Precedent transactions
- `data/process_data.json` — Process timeline data

---

## Question 1: Sell-Side Process Setup
```
Prepare process letter for CloudSoft secondaries.

Reference: data/precedent_transactions.csv, data/process_data.json

From data/precedent_transactions.csv:
- CloudSoft: Deal $420M, Revenue Multiple 8.2x, Status Announced

From data/process_data.json:
- Process Type: Sell-side
- Stage: Secondaries
- Timeline: First round Jan 15, Final bids Mar 15

Please:
1) Draft IOI process letter
2) Outline bid instructions
3) Set up timeline management
4) Track participant status
```

## Question 2: Valuation Benchmarking
```
Benchmark CloudSoft against precedent transactions.

Reference: data/precedent_transactions.csv

From data/precedent_transactions.csv:
- TechCo: 4.5x revenue (Technology)
- CloudSoft: 8.2x (Cloud SaaS)
- DataFlow: 6.1x (Data Analytics)

Please:
1) Assess multiple appropriateness
2) Compare growth profiles
3) Recommend valuation range
4) Flag any anomalies
```

## Question 3: Build a buyer list for sell-side mandate
```
Build a buyer list of potential acquirers for CloudSoft's sell-side process. Identify strategic and financial buyers, assess fit, and prioritize outreach.

Reference: data/precedent_transactions.csv, data/process_data.json

Please:
1) Identify strategic acquirers in the cloud/SaaS space
2) Add financial sponsors with relevant deal history
3) Score each buyer by strategic fit and ability to pay
4) Recommend outreach sequence
```

## Question 4: 解读并购新闻——对 Premier 投资者意味着什么
```
我持有 TechGlobal (TECH) 的股票，该公司刚宣布收购 DataFlow Systems。请帮我分析这对我意味着什么。

Reference: data/premier_ma_scenario.json, data/precedent_transactions.csv

From data/premier_ma_scenario.json:
- TechGlobal (我的持仓，成本价 $62）收购 DataFlow
- 收购价：每股 $30.75（现金 $18 + 0.15 股 TechGlobal 股票）
- 对 DataFlow 溢价：对比前收盘价 -3.9%，对比 30 日均价 +12.5%
- 协同效应：年营收协同 $85M，成本协同 $120M
- 第 3 年预计 EPS 增厚 $0.35

From data/precedent_transactions.csv:
- 类似交易的估值倍数参考

Please:
1) 分析这笔交易的战略逻辑（TechGlobal 为什么买 DataFlow）
2) 评估收购价格是否合理（对比先例交易倍数）
3) 分析协同效应是否可信——哪些协同容易实现，哪些较难
4) 计算交易对 TechGlobal 的财务影响（新增债务/股权摊薄/EPS 影响）
5) 作为 TechGlobal 股东，我应该支持还是反对这笔收购
6) 如果我是 DataFlow 股东，这个价格是否应该接受
7) 给出对持仓的影响评估和可能的行动建议
8) 标注需要关注的风险：整合风险/文化冲突/客户流失/竞对反应
```

## Question 5: 并购套利——Premier 如何利用并购事件
```
有一个正在进行的并购交易，请帮我分析是否存在并购套利机会。

Reference: data/premier_ma_scenario.json

假设当前市场情况（演示用，非从文件读取）：
- TECH 当前股价 $82.00（比公告日 $85 下跌 3.5%）
- FLOW 当前股价 $28.50（比隐含价值 $30.75 折价 7.3%）
- 预计交易完成时间：6 个月
- 交易风险：需要监管审批（Hart-Scott-Rodino）

Please:
1) 计算当前套利价差（FLOW 的当前价与隐含收购价之差）
2) 将价差年化（6 个月持有期），计算年化套利收益率
3) 评估交易失败风险（监管/股东投票/融资条件/反垄断）
4) 给交易成功概率打分（考虑反垄断风险）
5) 计算风险调整后的预期收益率
6) 如果决定参与套利，建议仓位大小和 hedge 策略
7) 解释并购套利的风险：交易失败风险/时间风险/竞购风险
8) 对比买卖双方的套利策略差异
```
