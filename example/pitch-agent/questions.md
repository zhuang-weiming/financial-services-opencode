# Pitch-Agent Agent — Example Questions

> **Routing trigger keywords:** pitch deck, pitch, comps analysis, DCF model, LBO model, buy-side pitch, deck refresh, IB check deck

**Data Files:**
- `data/growth_equity_deals.csv` — Growth equity comps
- `data/pitch_content.json` — Pitch content for Cloudflare

---

## Question 1: Cloud Infrastructure Pitch
```
Build a buy-side pitch for Cloudflare (NET-US).

Reference: data/growth_equity_deals.csv, data/pitch_content.json

From data/growth_equity_deals.csv:
- Cloudflare: Growth 40%, EV/Revenue 12x, EV/EBITDA 45x
- Market Share: 5%

From data/pitch_content.json:
- Thesis: Security and network edge computing leader
- Highlights: 40% growth, positive OCF, NRR >120%
- Concerns: Competitive pressure, stretched valuation

Please:
1) Structure investment thesis
2) Build valuation framework
3) Propose position sizing
4) Outline risk factors
```

## Question 2: Comp Set Analysis
```
Compare growth equity opportunities.

Reference: data/growth_equity_deals.csv

From data/growth_equity_deals.csv:
- Datadog: Growth 45%, EV/Rev 15x
- Snowflake: Growth 50%, EV/Rev 18x
- MongoDB: Growth 35%, EV/Rev 8x

Please:
1) Normalize multiples by growth
2) Rank opportunity by risk/reward
3) Recommend top 2 names
4) Suggest allocation weights
```

## Question 3: Build a football field valuation
```
Build a football field valuation for the target, showing DCF, comps, and LBO ranges.

Reference: data/growth_equity_deals.csv, data/pitch_content.json

Please:
1) Calculate DCF-derived valuation range
2) Add trading comps range
3) Add transaction comps range
4) Show final football field with weighted recommendation
```

## Question 4: Premier ETF 核心-卫星组合构建方案
```
请为一位 Premier 客户设计一个 ETF 核心-卫星投资组合，并作为投资建议呈报。

Reference: data/premier_etf_pitch_data.csv, data/pitch_content.json

From data/premier_etf_pitch_data.csv:
- 10 只 ETF，覆盖股票/债券/REITs/商品/国际/新兴市场
- 包含 1/3/5 年收益率、最大回撤、费率、波动率等数据

假设客户信息：
- 资产规模：1000 万元
- 投资目标：长期增长+适度收入
- 风险承受能力：中等
- 投资期限：10 年以上

Please:
1) 设计一个核心-卫星组合方案（核心 70-80% + 卫星 20-30%）
2) 从候选池中选择具体 ETF 及配比
3) 用历史数据回测组合（近 3 年/5 年收益、波动、回撤）
4) 与简单 60/40 基准组合做对比
5) 计算组合的综合费率
6) 写一段投资理念说明（为什么这样配、适用场景、局限）
7) 给出再平衡规则（何时/以什么阈值再平衡）
8) 风险提示：该组合在什么市场环境下可能表现不佳
```

## Question 5: Premier 持仓估值足球场
```
我关注的一只股票目前市场价 $155，请用多种估值方法构建足球场视图。

Reference: data/premier_etf_pitch_data.csv, data/pitch_content.json

假设目标公司（演示用，非从文件读取）：
- 当前股价：$155
- EPS(TTM)：$8.20
- BV/股：$25.50
- EBITDA/股：$15.80
- FCF/股：$6.50
- 营收/股：$45.00
- 增长率：12%
- 同行业平均 PE：22x，中位数：20x
- 同业平均 EV/EBITDA：14x，中位数：13x
- WACC：10%
- 高增长期：5 年，之后增长 4%

Please:
1) 用 DCF 估值计算内在价值区间
2) 用市盈率法（对标同行业 PE 区间 18-25x）估值
3) 用 EV/EBITDA 法（对标同业 12-16x）估值
4) 用 PB 法估值
5) 用 PEG 法（PEG < 1 为低估）估值
6) 将上述方法汇总为足球场图（每种方法的估值区间 + 当前价标注）
7) 分析各种方法的分歧在哪里，哪个更可靠
8) 给出综合估值判断和投资建议
```
