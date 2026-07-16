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
