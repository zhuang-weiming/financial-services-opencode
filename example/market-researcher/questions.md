# Market-Researcher Agent — Example Questions

> **Routing trigger keywords:** sector overview, industry overview, sector research, competitive landscape, market landscape, competitive analysis, industry deep dive, thematic research, idea generation

**Data Files:**
- `data/sector_comps.csv` — Sector comparable companies
- `data/sector_research.json` — Sector research

---

## Question 1: Cloud Infrastructure Sector Overview
```
Build a cloud infrastructure sector overview.

Reference: data/sector_comps.csv, data/sector_research.json

From data/sector_comps.csv:
- Cloudflare: Revenue $1.85B, Growth 40%, Share 5%
- Datadog: Revenue $2.1B, Growth 45%, Share 8%
- Snowflake: Revenue $3.2B, Growth 50%, Share 6%

From data/sector_research.json:
- Market Size: $180B current → $320B FY27 (12% CAGR)
- Key Themes: AI demand, multi-cloud, edge, security

Please:
1) Map competitive positioning
2) Size addressable market
3) Identify secular trends
4) Recommend sector weighting
```

## Question 2: Competitive Analysis
```
Analyze competitive dynamics in cloud infra.

Reference: data/sector_comps.csv

From data/sector_comps.csv:
- Leaders vs challengers structure
- Market share data

Please:
1) Build competitive matrix
2) Assess moat strength per player
3) Identify winner/loser trends
4) Draft sector allocation view
```

## Question 3: What are the top 5 themes
```
What are the top 5 themes driving the cloud infrastructure sector in 2026?

Reference: data/sector_research.json

Please:
1) Rank themes by revenue impact
2) Identify which are accelerating vs maturing
3) Map each theme to listed beneficiaries
4) Recommend how to position for them
```

## Question 4: 2026 下半年 Premier 投资趋势地图
```
作为一位 Premier 投资者，请为我绘制 2026 年下半年的投资趋势全景图。

Reference: data/premier_trends_2026H2.json, data/sector_research.json

From data/premier_trends_2026H2.json:
- 5 大趋势：AI 应用落地、利率下行、消费复苏、能源转型 2.0、银发经济
- 每个趋势包含受益标的、风险因素、建议行动

From data/sector_research.json:
- 云基础设施市场 1800 亿 -> 3200 亿（12% CAGR）

Please:
1) 按确定性× 影响力两个维度对 5 大趋势进行四象限排序
2) 趋势 1（AI）+ 趋势 2（利率下行）的交叉影响分析
3) 每个趋势对应的具体可投资标的（A股/美股/ETF 三层映射）
4) 建议的资产配置权重调整（在当前基准上增减）
5) 标注各个趋势的风险触发条件（什么情况下应该减仓）
6) 生成一个简洁的"趋势-标的-行动"对照表
```

## Question 5: A 股行业轮动信号分析
```
请分析当前 A 股市场的行业轮动状态，为我的 Premier 组合提供板块配置建议。

Reference: data/sector_comps.csv

From data/sector_comps.csv:
- Cloudflare/Datadog/Snowflake：云基础设施参考
- 我需要扩展到 A 股申万一级行业的分析

假设当前行业表现数据如下：
- 近 3 月领涨行业：银行（+12%）、公用事业（+9%）、煤炭（+8%）
- 近 3 月垫底行业：计算机（-5%）、医药（-3%）、传媒（-2%）
- 近 1 月出现轮动迹象：电子（+6%）、电力设备（+4%）开始走强

Please:
1) 分析当前行业轮动所处阶段（复苏早期/过热/衰退/滞胀映射的行业表现）
2) 识别最近 3 个月 vs 1 个月领涨行业的切换信号
3) 判断轮动是否持续还是短期反弹
4) 给出超配/标配/低配的行业建议
5) 推荐具体的行业 ETF 或主题基金
6) 标注轮动加速或逆转的关键观察指标
```
