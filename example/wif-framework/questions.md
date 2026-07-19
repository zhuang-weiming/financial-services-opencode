# WIF Framework Cookbook — Example Questions

> **Routing trigger keywords:** WIF, wealth investment framework, fund advisory methodology, asset allocation portfolio, portfolio health status, phase assessment

**Data Files:**
- `data/_merged_prices_20260716.csv` — 4926×10 merged price matrix (2007-01-03 to 2026-07-16)
- `data/WIF_v59_nav_20260716.csv` — Backtest NAV series
- `data/WIF_v59_trade_log_20260716_HSCBC.csv` — Historical trade log
- `data/WIF_v59_Report_20260716.html` — Full backtest report with Chart.js
- `data/tickers_20260716/` — 48 individual ticker CSV files with WIF-standard column names

---

## Question 1: Portfolio Health Status
```
Using the WIF v5.9 framework data, assess the current portfolio health status.

Reference: data/_merged_prices_20260716.csv, data/WIF_v59_trade_log_20260716_HSCBC.csv

From the WIF framework:
- The latest data is 2026-07-16
- Phase 1 criteria: F29 > 150bp, VIX < 25%, VIXTERM > 0

Please:
1) Calculate current Phase (1-5) with supporting evidence
2) Report FFR, F29, VIX spot, VIX3M proxy, VIXTERM values
3) Compare current allocation to WIF target weights for current phase
4) Flag any regime transition signals
```

## Question 2: Asset Allocation Recommendation
```
Generate an asset allocation proposal using the WIF v5.9 methodology.

Reference: data/_merged_prices_20260716.csv

From the WIF framework:
- The methodology defines 5 market phases (1=Rising, 2=Panic, 3=Fall, 4=Recover, 5=Transition)
- Each phase has a distinct multi-asset ETF portfolio allocation
- Phase is determined by F29 (Fed Funds 29-week change), VIX, and VIXTERM

Assuming the latest data indicates Phase [1-5]:

Please:
1) Determine current phase from the data
2) Show the WIF target allocation for that phase (equity, fixed income, commodity, REIT weights)
3) Recommend specific ETFs from the 40-ticker universe
4) Provide a rebalancing plan if the actual portfolio deviates
```

## Question 3: Backtest Performance Review
```
Review the WIF v5.9 backtest results and analyze the strategy's performance characteristics.

Reference: data/WIF_v59_nav_20260716.csv, data/WIF_v59_trade_log_20260716_HSCBC.csv

From the backtest results:
- Period: 2007-01-03 to 2026-07-16 (19.5 years)
- Ticker: HSCBC (0.20% management fee)
- Friction costs included

Please:
1) Calculate CAGR, Sharpe ratio, max drawdown
2) Identify the number of trades and total friction cost
3) Show the trade sequence with dates and rationale
4) Compare performance in each market phase regime
5) Assess whether the methodology added value vs buy-and-hold
```

## Question 4: Risk Regime Analysis
```
Analyze the current risk regime using the WIF framework's macro indicators.

Reference: data/tickers_20260716/DGS10_2007_2026.csv, data/tickers_20260716/BAMLH0A0HYM2_2007_2026.csv

Please:
1) Calculate the current credit spread (BAA - DGS10)
2) Assess yield curve shape (10Y-2Y spread)
3) Compare current VIX level to historical percentiles
4) Determine which WIF risk regime we are in
5) Flag any divergence between macro indicators and current Phase
```

## Question 5: Premier 个人 WIF 资产配置方案
```
作为一位 Premier 客户，请使用 WIF v5.9 框架为我生成当前市场环境下的个人资产配置方案。

Reference: data/_merged_prices_20260716.csv, data/WIF_v59_nav_20260716.csv

我从您已有的数据理解，WIF 框架通过 F29/VIX/VIXTERM 判断 5 个市场阶段。

Please:
1) 判断当前处于哪个市场阶段（Phase 1-5），并列出 F29、VIX、VIXTERM 的具体数值
2) 说明该阶段对应的默认资产配置比例（权益/固收/商品/REITs）
3) 根据一个假设的 Premier 风险偏好（中等风险承受能力）微调配置比例
4) 从 WIF 40-ETF 候选池中推荐具体 ETF 及配比
5) 如果当前组合与此目标配置偏差超过 5%，给出再平衡交易指令
6) 标注当前是否处于阶段转换预警区
```

## Question 6: WIF 框架在 A 股市场的适用性讨论
```
我是一位关注 A 股市场的 Premier 投资者。WIF 框架基于美国市场开发，请帮我分析如何将其应用于 A 股投资。

Please:
1) 分析 WIF 框架核心指标（F29/VIX/VIXTERM）在 A 股市场的适用性
2) 如果 A 股没有合适的 VIX 替代指标，推荐哪些本土化指标（如 50ETF 期权隐含波动率/北向资金/融资融券比）
3) 设计一个简化版 A 股 WIF 框架：用申万行业指数替换标普行业 ETF
4) 回测思路：如何改造回测引擎对比 A 股 WIF 策略 vs 沪深 300 买入持有
5) 给出 Premier 投资者在实际使用时应做的最小调整清单
```
