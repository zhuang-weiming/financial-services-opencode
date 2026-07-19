# Backtest-Builder Agent — Example Questions

> **Routing trigger keywords:** backtest, strategy backtest, signal test, strategy test, walk-forward, backtest diagnose, strategy development

**Data Files:**
- `data/strategy_results.csv` — Strategy backtest results
- `data/backtest_config.json` — Backtest configuration parameters

---

## Question 1: CSI 300 Momentum Backtest
```
Run a backtest on CSI 300 momentum strategy from 2023 to 2025.

Reference: data/strategy_results.csv, data/backtest_config.json

From data/backtest_config.json:
- Universe: CSI 300
- Strategy: 12M Momentum
- Period: 2023-01-01 to 2025-12-31
- Rebalance: Monthly
- Slippage: 0.1%

Please:
1) Run the momentum backtest
2) Show Sharpe ratio and max drawdown
3) Plot equity curve
4) Compare to buy-and-hold benchmark
```

## Question 2: Mean Reversion on S&P 500
```
Test a mean-reversion strategy on the S&P 500 universe.

Reference: data/strategy_results.csv, data/backtest_config.json

Please:
1) Configure 5-day overbought/oversold signals
2) Run backtest with 0.05% slippage assumption
3) Report Sharpe, Sortino, Calmar ratios
4) Show monthly returns heatmap
```

## Question 3: Walk-forward analysis on crypto strategy
```
Run a walk-forward analysis on my crypto momentum strategy, using 2-year train / 6-month test windows.

Reference: data/backtest_config.json

Please:
1) Set up 3-fold walk-forward structure
2) Run each fold and report out-of-sample performance
3) Compare walk-forward results to full-sample backtest
4) Flag any overfitting concerns
```

## Question 4: 定投 vs 择时 vs 买入持有——世纪对决
```
请帮我回测对比四种经典投资策略在 2015-2026 年间的表现。

Reference: data/premier_dca_config.json

From data/premier_dca_config.json:
- 策略 A：每月固定定投 10000 元
- 策略 B：大跌加仓法（基础定投 5000 + 跌幅>5%加仓 10000）
- 策略 C：200 日均线择时（线上全仓/线下现金）
- 策略 D：2015 年初一次性买入持有
- 标的：标普 500 ETF
- 总投入约 120 万（策略 D 一次性，其它为累计）

Please:
1) 回测 4 种策略在 2015-2026 年的总收益、年化收益
2) 计算各策略的夏普比率、最大回撤、收益/回撤比
3) 按不同市场阶段（牛市/熊市/震荡市）分段对比
4) 计算定投策略的平均持仓成本，与一次性买入的成本对比
5) 对策略 B（大跌加仓法）做敏感性分析：不同跌幅阈值的效果
6) 给出针对 Premier 投资者的建议：什么情况下选哪种策略
7) 标注回测的局限性（幸存者偏差、参数过拟合等）
```

## Question 5: "我有个选股想法"——回测验证我的逻辑
```
我有一个选股逻辑：当某只股票的 RSI(14) < 30 且 成交量是 20 日均量的 1.5 倍以上时买入，RSI > 70 时卖出。请帮我验证这个策略。

Reference: data/premier_dca_config.json (for config format reference)

假设您在沪深 300 成分股中测试此策略，回测期间 2020-2026。

Please:
1) 将我的选股逻辑转化为可执行的策略信号
2) 回测 2020-2026 年期间在沪深 300 上的表现
3) 报告胜率、平均盈亏比、夏普比率、最大回撤
4) 分析该策略在不同市场阶段（上涨/下跌/震荡）的有效性
5) 检查策略的换手率和交易成本影响
6) 建议参数优化方向（RSI 阈值、成交量倍数等）
7) 给出是否存在过拟合风险的判断
8) 如果策略有效，建议实盘使用时需要注意什么
```
