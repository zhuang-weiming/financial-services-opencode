# Wealth-Management Agent — Example Questions

> **Routing trigger keywords:** client report, client review, financial plan, retirement plan, investment proposal, portfolio rebalance, tax-loss harvesting, wealth management

**Data Files:**
- `data/client_profiles.csv` — Client profiles
- `data/meeting_prep.json` — Meeting preparation data

---

## Question 1: Client Review Meeting
```
Prepare for a client review meeting with Meridian Family Office.

Reference: data/client_profiles.csv (row 2), data/meeting_prep.json

From data/client_profiles.csv:
- Client: Meridian Family Office
- Total Assets: $8,500,000
- Risk Tolerance: Moderate

From data/meeting_prep.json:
- Meeting Date: 2024-04-20
- Portfolio Value: $8.5M
- YTD Return: +9.0%
- Benchmark: +7.2%
- Active Return: +0.4%

Allocation:
- US Large Cap: 35%
- Intl Developed: 20%
- Emerging Markets: 10%
- US Fixed Income: 25%
- Alternatives: 10%

Key Updates:
- Client's son starting college next fall ($60K/year)
- Client inherited $500K (seeking guidance)
- Interest in sustainable investing has increased

Please:
1) Prepare performance attribution summary
2) Analyze drift from target allocation
3) Draft discussion agenda
4) Identify action items for follow-up
```

## Question 2: Tax-Loss Harvesting
```
Identify tax-loss harvesting opportunities from the portfolio.

Reference: data/meeting_prep.json

From data/meeting_prep.json:
- Portfolio Value: $8.5M
- YTD Return: +9.0%
- Sleeve Returns: Mixed (US Large Cap +8.5%, EM +3.8%)

Please:
1) Identify positions with losses to harvest
2) Suggest replacement securities
3) Model wash sale window considerations
4) Calculate expected tax benefit
5) Draft harvesting plan with timeline
```

## Question 3: Run tax-loss harvesting on taxable account
```
Run tax-loss harvesting analysis on the taxable account, flagging any wash sale risks.

Reference: data/meeting_prep.json

Please:
1) Scan all taxable positions for unrealized losses
2) Prioritize losses by size and tax benefit
3) Suggest suitable replacement ETFs/stocks
4) Build a harvesting schedule respecting wash sale rules
```

## Question 4: 基金组合诊断与优化
```
作为一位 Premier 客户，请对我的基金持仓进行全面诊断并提出优化建议。

Reference: data/premier_fund_holdings.csv, data/meeting_prep.json

From data/premier_fund_holdings.csv:
- 总持仓：8 只基金/ETF，覆盖混合型、指数型、QDII、行业主题
- 配置比例从 8% 到 20% 不等
- 部分基金有显著未实现盈亏

From data/meeting_prep.json:
- 总资产：$8.5M
- 风险承受能力：中等

Please:
1) 分析当前组合的资产配置结构（权益/固收/海外/行业集中度）
2) 评估每只基金的费率合理性（对比同类中位数）
3) 检查风格箱分布和风格漂移风险
4) 识别持仓重叠和行业集中风险
5) 给出具体的调仓建议（卖出/持有/加仓）及理由
6) 推荐替代基金或 ETF 方案
```

## Question 5: 投资理念诊断与行为偏误分析
```
请通过投资理念自测问卷分析我的投资风格，并结合实际持仓行为诊断潜在的行为偏误。

Reference: data/premier_philosophy_quiz.json, data/premier_fund_holdings.csv

From data/premier_philosophy_quiz.json:
- 5 道自测题，覆盖风险偏好、选基逻辑、长期态度、创新接受度、收益预期
- 输出维度：价值型 / 成长型 / 均衡型 / 趋势型 / 保守型

From data/premier_fund_holdings.csv:
- 当前持仓数据含每只基金的成本和盈亏

Please:
1) 根据我的回答计算各投资风格分数，判断主导风格
2) 分析主导风格的特点和适用市场环境
3) 对比我的实际持仓行为，检查是否知行合一
4) 诊断可能存在的行为偏误（处置效应/过度自信/锚定效应/追涨杀跌）
5) 给出针对性的行为矫正建议
6) 提供与我的风格匹配的参考组合配置
```
