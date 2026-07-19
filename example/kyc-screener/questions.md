# KYC-Screener Agent — Example Questions

> **Routing trigger keywords:** KYC, onboarding, AML screening, AML, watchlist screening, enhanced due diligence, client screening

**Data Files:**
- `data/client_onboarding.csv` — Client onboarding records
- `data/watchlist_results.json` — Watchlist screening results

---

## Question 1: Client Onboarding Screening
```
Screen new client Harborview Endowment against watchlists.

Reference: data/client_onboarding.csv (row 1), data/watchlist_results.json

From data/client_onboarding.csv:
- Client: Harborview Endowment
- Risk Rating: Medium
- Account Type: Institutional

From data/watchlist_results.json (index 1):
- Name: Maria Santos
- Type: Individual
- List: EU Sanctions
- Match Confidence: 72%
- Status: cleared

Please:
1) Parse the client onboarding record
2) Cross-reference against watchlist results
3) Assign risk rating based on firm rules
4) Flag any items requiring enhanced due diligence
```

## Question 2: Enhanced Due Diligence Review
```
Review Alpha Trading Ltd for potential high-risk designation.

Reference: data/client_onboarding.csv, data/watchlist_results.json

From data/watchlist_results.json:
- Name: Alpha Trading Ltd
- Type: Entity
- List: FATF High-Risk
- Match Confidence: 88%
- Status: enhanced_due_diligence

Please:
1) Document the watchlist match details
2) Apply firm KYC rules for high-risk entities
3) Determine required documentation
4) Draft escalation if needed
```

## Question 3: What is the firm's EDD procedure for PEPs?
```
What is the firm's enhanced due diligence procedure for Politically Exposed Persons (PEPs)?

Reference: data/watchlist_results.json

Please:
1) Locate the PEP policy in the firm's KYC rules
2) Summarize the enhanced documentation requirements
3) List additional screening steps required
4) Flag any jurisdictions with automatic escalation
```

## Question 4: Premier 客户适当性快速检查
```
请对一位 Premier 客户做适当性检查，确认现有持仓是否符合其风险测评结果。

Reference: data/premier_suitability.csv, data/client_onboarding.csv

From data/premier_suitability.csv:
- 5 种风险类型的配置限制矩阵
- 稳健型：权益 <=50%，固收 >=30%，单个 <=8%，EM <=10%

From data/client_onboarding.csv:
- Harborview Endowment：中等风险（映射到均衡型）

假设需要检查的客户数据：
- 风险测评结果：均衡型
- 当前配置：权益 68%、固收 18%、另类 14%
- 单只最大持仓：茅台 12.5%
- 新兴市场占比：8%
- 持有少量 crypto（比特币占 2%）

Please:
1) 将客户的风险测评等级映射到适当性规则
2) 逐一检查每个维度的合规性（权益上限/债券下限/集中度/新兴市场/crypto）
3) 标记不符合的项目，说明违反了什么规则及风险
4) 对每个违规项给出修正建议
5) 形成一份适当性检查报告（通过/带条件通过/不通过）
6) 如果客户希望维持现有配置但超限，需要做什么签批流程
```

## Question 5: 跨境投资的合规路线图
```
我想投资美股、港股和少量加密货币，请帮我梳理合规要求和操作路径。

Reference: data/premier_suitability.csv, data/watchlist_results.json

From data/premier_suitability.csv:
- 均衡型客户：crypto 为"Limited"
- 权益投资无地域限制标注

From data/watchlist_results.json:
- 参考 KYC 筛查流程

Please:
1) 境内投资境外市场的合规路径（QDII 基金/港股通/收益互换/跨境理财通）
2) 美股投资：如何开户（富途/老虎/盈透/嘉信各方案对比）
3) 港股投资：港股通 vs 直接港股券商对比
4) 加密货币：合规的交易平台和出入金路径（香港持牌交易所 vs 海外平台）
5) 各路径的费用、门槛、便捷度对比
6) 税务考虑：资本利得税/股息税/遗产税（中美港差异）
7) 资金出入境的外汇管制限制（每人每年 5 万美元额度如何管理）
8) 推荐一个分步推进的路线图：先做什么、再做什么
```
