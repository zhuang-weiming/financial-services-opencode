# Factor-Researcher Agent — Example Questions

> **Routing trigger keywords:** factor research, factor analysis, correlation analysis, IC/IR, quantile backtest, factor decomposition, risk decomposition, performance attribution

**Data Files:**
- `data/factor_ic_data.csv` — Factor IC time series
- `data/factor_correlation.json` — Factor correlation matrix

---

## Question 1: IC/IR Analysis on Momentum
```
Run IC/IR analysis on the momentum factor across the A-share universe.

Reference: data/factor_ic_data.csv

From data/factor_ic_data.csv:
- Factor: Momentum (12M-1M)
- Universe: CSI 300
- Period: 2020-2026
- IC time series: monthly values

Please:
1) Calculate mean IC, IC std, and IR
2) Show IC time-series chart
3) Test for statistical significance
4) Flag any periods of factor failure
```

## Question 2: Factor Correlation Analysis
```
How correlated are momentum and reversal factors? Display a correlation matrix.

Reference: data/factor_correlation.json

From data/factor_correlation.json:
- Factors: Momentum, Reversal, Value, Size, Quality
- Correlation pairs: 5×5 matrix

Please:
1) Display full correlation matrix
2) Identify highly correlated factor pairs (>0.6)
3) Suggest factor combinations that provide diversification
4) Recommend orthogonalization if needed
```

## Question 3: Fama-French decomposition on AAPL
```
Run a Fama-French 3-factor decomposition on AAPL to understand its risk exposures.

Reference: data/factor_ic_data.csv

Please:
1) Regress AAPL returns on Market, SMB, HML factors
2) Report factor loadings with t-statistics
3) Calculate alpha (abnormal return)
4) Show R-squared and interpretation
```

## Question 4: Premier 组合因子暴露诊断
```
请对我的 Premier 投资组合进行全面的因子暴露分析。

Reference: data/premier_portfolio_factors.csv

From data/premier_portfolio_factors.csv:
- 10 只持仓（A股+美股混合组合）
- 每个股票在 7 个因子上的暴露得分（-1 到 +1）
- 各股票配置权重从 3.8% 到 21.2%

Please:
1) 计算组合层面各因子的加权暴露得分
2) 用雷达图或柱状图展示因子暴露剖面
3) 识别是否存在某一因子过度集中（如动量/Momentum 暴露偏高）
4) 分析因子暴露的集中度——组合的 alpha 来源是否过度依赖少数因子
5) 建议增加哪些低相关因子的暴露来改善分散化
6) 给出具体的调仓建议（卖出哪些、买入哪些）来优化因子结构
7) 诊断在当前市场环境下，哪些因子暴露可能面临风险
```

## Question 5: 因子相关性崩溃预警分析
```
市场剧烈波动时期因子相关性往往趋同，请分析我的组合是否面临这种风险。

Reference: data/premier_portfolio_factors.csv

From data/premier_portfolio_factors.csv:
- 当前组合的因子暴露结构
- 需要分析正常市和压力市下的因子相关变化

假设极端情景：
- 情景 A：利率急升 100bp（动量因子和价值因子相关性从 0.1 升到 0.6）
- 情景 B：科技股暴跌 20%（成长因子和动量因子相关性从 0.3 升到 0.8）

Please:
1) 计算正常市场环境下因子两两之间的相关性矩阵
2) 分析压力情景下哪些因子相关性可能急剧升高
3) 评估我的组合在压力情景下的有效分散度下降程度
4) 建议哪些低相关/负相关因子可以作为"危机 alpha"
5) 给出一个"压力测试版"组合，在极端市况下仍能保持分散化
6) 推荐可操作的避险 ETF 或策略
```
