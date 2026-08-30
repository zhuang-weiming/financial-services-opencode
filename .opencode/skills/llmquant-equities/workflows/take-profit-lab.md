---
name: Take-Profit Lab
description: Analyze whether a ticker is suitable for long-term holding or needs systematic profit-taking using LLMQuant Data historical simulations.
input_data_source: LLMQuant Data
pack: research
---

# Take-Profit Lab

## Purpose

Quantify exit discipline for a stock or ETF: hold forever, tier out, sell all at milestones, use trailing stops, or combine profit-taking with hedges.

## Input Data Source

Use **LLMQuant Data** for historical prices, volatility, corporate actions, and exit-strategy simulations.

## Data Needed

Required LLMQuant Data inputs:
- equity price history adjusted for dividends and splits.
- equity market snapshot data for current price and liquidity.
- realized volatility history for realized volatility and drawdown behavior.
- strategy exit-rule backtest data for entry cohorts, exit rules, CAGR, max drawdown, win rate, and path dependency metrics.

Core metrics:
- Rollercoaster rate: share of entry cohorts that reached a major gain and then gave back a large fraction of peak profit.
- Hold CAGR and max drawdown.
- Median and tail outcomes for each exit strategy.
- Active-exit improvement or drag versus hold.

## Workflow

1. Pull adjusted history and define the simulation window.
2. Run hold, tiered exits, full-sale triggers, trailing stops, and volatility-aware exits.
3. Compare return, drawdown, and path pain rather than only CAGR.
4. Classify the instrument as holdable, tiered-exit preferred, or structurally unsuitable for buy-and-hold.
5. Translate the winning rule into concrete levels from the user's cost basis when provided.

## Output Format

1. **Exit Verdict**: hold, tier, strict exit, or avoid long hold.
2. **Headline Metrics**: CAGR, max drawdown, rollercoaster rate, sample size, period.
3. **Strategy Table**: return, drawdown, rollercoaster rate by rule.
4. **Action Plan**: sell levels, trailing stop, review cadence.
5. **Data Used**.

## Guardrails

- Do not recommend exits from unadjusted price data.
- Do not overfit to the single best backtest rule without showing alternatives.
- For leveraged ETFs, explicitly discuss volatility decay and path dependency.
