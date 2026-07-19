# Alpha-Researcher Agent — Example Questions

> **Routing trigger keywords:** alpha, alpha zoo, alpha family, factor bench, factor benchmark, IC/IR, alpha research, factor research

**Data Files:**
- `data/alpha101_bench.csv` — Alpha101 factor benchmark results
- `data/qlib158_summary.json` — Qlib158 alpha family summary

---

## Question 1: List all alpha families
```
List all alpha families available in the alpha zoo, with a brief description of each.

Reference: data/alpha101_bench.csv, data/qlib158_summary.json

From data/alpha101_bench.csv:
- 101 alphas across multiple families
- Performance metrics per alpha

From data/qlib158_summary.json:
- Qlib158: 158 quantitative research alphas
- Coverage: cross-sectional factor libraries

Please:
1) List all 5 alpha families with name and count
2) Describe the origin of each family
3) Note which markets each family is designed for
4) Suggest which family to start with for A-share vs US research
```

## Question 2: Bench the alpha101 family against CSI 300
```
Run a factor bench on the alpha101 family against the CSI 300 universe.

Reference: data/alpha101_bench.csv

Please:
1) Compute IC and IR for each of the 101 alphas
2) Rank top 20 by IC
3) Rank top 20 by IR
4) Show the distribution of IC values across the family
5) Flag alphas with unstable or negative IC
```

## Question 3: Compare IC/IR between alpha families
```
Compare IC/IR between the gtja191 and fundamental factor families to identify which has stronger predictive power.

Reference: data/alpha101_bench.csv, data/qlib158_summary.json

Please:
1) Compute mean IC and IR for each family
2) Show IC time-series stability comparison
3) Identify the top 5 alphas across all families by IR
4) Recommend which family is best suited for the current market regime
```

## Question 4: 因子投资入门——哪些因子适合个人投资者
```
我是一位对量化投资感兴趣的 Premier 投资者，想了解因子投资如何应用于我的组合。

Reference: data/premier_factor_portfolio.csv, data/alpha101_bench.csv

From data/premier_factor_portfolio.csv:
- 8 个常见因子的 IC 值（在沪深 300 和标普 500 上）
- 每个因子有可投资的 ETF 映射
- 统计显著性标注

From data/alpha101_bench.csv:
- alpha101 家族的因子表现基准

Please:
1) 用通俗语言解释每个因子的含义和投资逻辑
2) 对比沪深 300 和标普 500 上各因子的有效性差异
3) 指出哪些因子对个人投资者最实用（考虑可投资性、费用、复杂度）
4) 推荐一个 3-5 因子的简化组合，给出建议权重和对应 ETF
5) 说明因子投资的常见陷阱（拥挤交易/因子失效/换手率过高）
6) 建议个人投资者如何定期检视因子暴露并再平衡
```

## Question 5: 简化的多因子打分模型实战
```
请帮我构建一个简易的多因子打分模型，用于筛选沪深 300 中的优质标的。

Reference: data/premier_factor_portfolio.csv

假设我有一个 50 万元的 A 股组合，想用因子方法替代主观选股。

Please:
1) 从 alpha101 或 qlib158 家族中选择适合 A 股的 3-5 个 alpha
2) 解释每个 alpha 的计算逻辑和适用条件
3) 构建简化的多因子打分模型（等权或 IC 加权）
4) 用假设数据演示打分排名前 10 的股票
5) 说明该模型的局限性和改进方向
6) 建议如何将打分结果转化为实际持仓决策
```
