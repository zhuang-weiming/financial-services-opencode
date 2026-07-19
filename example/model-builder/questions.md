# Model-Builder Agent — Example Questions

> **Routing trigger keywords:** DCF, LBO, 3-statement model, 3 statement model, comps, trading comps, valuation model

**Data Files:**
- `data/historical_data.csv` — Historical financial data
- `data/model_assumptions.json` — Model assumptions

---

## Question 1: Build 3-Statement Model
```
Build a 3-statement model for Sample Corp.

Reference: data/historical_data.csv, data/model_assumptions.json

From data/historical_data.csv:
- Q1 FY23 to Q1 FY24 quarterly data
- Revenue range: $2.1M - $2.6M
- EBITDA margin: ~24%

From data/model_assumptions.json:
- Revenue growth: 8%
- EBITDA margin: 24%
- Tax rate: 21%
- Capex: 8% of revenue
- Working capital: 7% of revenue

Please:
1) Build integrated IS/BS/CF model
2) Link all three statements
3) Balance the model
4) Add ratio analysis
```

## Question 2: Forecast Validation
```
Validate the Q1 FY24 forecast assumptions.

Reference: data/historical_data.csv

From data/historical_data.csv:
- Q1 FY24 Revenue: $2.62M
- Q1 FY24 EBITDA: $650K (25% margin)
- Q1 FY24 Cash Flow: $610K

Please:
1) Compare to historical trends
2) Assess margin sustainability
3) Flag any assumption changes
4) Update model if needed
```

## Question 3: Build an LBO model with 6x leverage
```
Build an LBO model with 6.0x leverage for the target company.

Reference: data/historical_data.csv, data/model_assumptions.json

Please:
1) Structure debt financing at 6.0x EBITDA
2) Model debt repayment schedule
3) Calculate IRR and MOIC across exit years
4) Show sensitivity to entry/exit multiples
```

## Question 4: 个人财务健康模型
```
请帮我构建一份个人财务三表模型，评估我的财务健康状况。

Reference: data/premier_personal_finance.csv

From data/premier_personal_finance.csv:
- 12 个月的收支和资产负债数据
- 月收入约 12-15 万，月支出约 9-12 万
- 金融资产约 300-350 万
- 房贷余额约 114-120 万
- 房产价值 500 万

Please:
1) 构建个人版的利润表（收入-支出=储蓄）、资产负债表和现金流量表
2) 计算关键财务健康指标：
   - 储蓄率（月储蓄/月收入）
   - 负债率（总负债/总资产）
   - 紧急备用金（流动资产/月支出）
   - 投资比率（金融资产/总资产）
3) 分析全年收入和支出的季节性
4) 评估当前的负债水平是否合理
5) 给出提升财务健康度的具体建议
6) 建议一个适合当前财务状况的资产配置方案
```

## Question 5: 理解杠杆收购——Premier 投资者视角
```
我投资的 PE 基金正在进行一笔 LBO 交易，请帮我理解这个交易对投资者的影响。

使用假设的 LBO 交易结构（非从文件读取）：

目标公司参数：
- 收购价：EBITDA 5000 万 × 8.5x = 4.25 亿
- 债务融资：70%（2.975 亿，利率 6.5%，5 年期）
- 股权投入：30%（1.275 亿，其中 PE 出资 60%，我和其他 LP 出资 40%）
- EBITDA 增长假设：年增 8%，第 5 年退出
- 退出倍数：10.0x EBITDA
- 管理费：每年 2%
- 业绩提成：超额收益的 20%

Please:
1) 构建还款时间表（5 年债务偿还计划）
2) 计算第 5 年退出时的 EBITDA
3) 计算退出时的企业价值和股权价值
4) 计算我的投资 IRR 和 MOIC（扣除管理费和业绩提成后）
5) 敏感性分析：退出倍数 ±2x × EBITDA 增长率 ±3%
6) 解释 LBO 交易的收益杠杆来自哪里（杠杆效应/经营改善/多重扩张）
7) 标注主要风险：再融资风险、经营不及预期、多重压缩
```
