# Financial-Analysis Agent — Example Questions

> **Routing trigger keywords:** 3-statement model, DCF, LBO, comps, comparable analysis, competitive analysis, financial model

**Data Files:**
- `data/airline_comps.csv` — Airline comparable companies
- `data/lbo_model.json` — LBO model data

---

## Question 1: Airline Comps Analysis
```
Analyze airline sector comparables.

Reference: data/airline_comps.csv

From data/airline_comps.csv:
- Delta: Revenue $50B, Margin 12%, EV/EBITDA 6.5x
- American: Revenue $45B, Margin 8%, EV/EBITDA 5.2x
- Southwest: Revenue $25B, Margin 6%, EV/EBITDA 4.8x
- United: Revenue $48B, Margin 10%, EV/EBITDA 6.0x

Please:
1) Normalize metrics for comparison
2) Identify multiple compression opportunities
3) Rank by operational efficiency
4) Recommend sector positioning
```

## Question 2: Delta LBO Returns Analysis
```
Analyze Delta LBO returns sensitivity.

Reference: data/lbo_model.json

From data/lbo_model.json:
- Entry Multiple: 8.5x EV/EBITDA
- Leverage: 70% debt, 30% equity
- Returns: IRR 18%, MOIC 2.3x
- Hold Period: 5 years

Please:
1) Build IRR sensitivity table
2) Test exit multiple scenarios
3) Stress-test leverage assumptions
4) Assess downside protection
```

## Question 3: Stress-test the DCF model under recession
```
Stress-test the DCF model under a recession scenario (-200bps GDP impact).

Reference: data/airline_comps.csv, data/lbo_model.json

Please:
1) Adjust revenue growth assumptions downward
2) Recalculate WACC with higher risk premium
3) Show impact on terminal value
4) Present a revised valuation range
```

## Question 4: 用 DCF 评估消费龙头——伊利股份
```
我持有伊利股份，请用 DCF 模型评估其内在价值。

Reference: data/premier_consumer_stock.csv

From data/premier_consumer_stock.csv:
- 近 7 年营收从 623 亿增长至 920 亿（CAGR ~6.7%）
- 利润率稳定，EBIT 利润率 ~10-11%
- Capex 约 6-7% 营收，DA 约 4-5%
- 净债务持续下降，从 450 亿降至 160 亿

估值假设：
- 营收增长率：未来 3 年 6%，3-5 年 5%，5 年后 3%
- EBIT 利润率维持 10.8%
- WACC：9%
- 终值增长率：3%

Please:
1) 计算未来 5 年的预测自由现金流
2) 计算终值（TV）
3) 折现并加总得到企业价值
4) 调整为股权价值，计算每股内在价值
5) 与当前市价对比，判断安全边际
6) 敏感性分析：WACC ±1% × 终值增长率 ±0.5%
7) 评估 DCF 模型的局限性及补充估值方法
```

## Question 5: 场景分析——Premier 大额支出对现金流的影响
```
我是一名 Premier 客户，未来 3 年有几项大额支出计划，请帮我做现金流影响分析。

Reference: data/premier_consumer_stock.csv (作为参考格式)

情景假设（非从 data 读取）：
- 流动资产：500 万元（含 200 万股票、150 万基金、150 万活期/理财）
- 年收入：120 万元（税后）
- 年支出：60 万元（日常）
- 未来大额支出：
  - 2027 年 9 月：子女出国留学首年费用 80 万元
  - 2028 年 6 月：换房首付 200 万元
  - 2029 年 12 月：父母养老社区一次性费用 100 万元

Please:
1) 建立未来 3 年的现金流预测表（月度）
2) 识别每个时间点的资金缺口/盈余
3) 建议如何提前安排资产变现计划（何时卖什么、卖多少）
4) 分析市场波动对变现计划的影响（如股市大跌时被迫卖出）
5) 给出不影响长期投资目标的优化方案
6) 建议应急流动性储备的最低额度
```
