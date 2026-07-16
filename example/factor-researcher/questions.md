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
