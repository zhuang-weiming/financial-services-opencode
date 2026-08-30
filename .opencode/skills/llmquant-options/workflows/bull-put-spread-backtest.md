---
name: Bull Put Spread Backtest
description: Backtest bull put spread rules with signal and no-signal controls using LLMQuant Data historical prices, IV, and option models.
input_data_source: LLMQuant Data
pack: trading
---

# Bull Put Spread Backtest

## Purpose

Test whether a bull put spread entry rule adds value versus a mechanical control, using consistent parameters, risk caps, and transparent trade ledgers.

## Input Data Source

Use **LLMQuant Data** for historical prices, IV history, signal history, option spread construction, and backtest results.

## Data Needed

Required LLMQuant Data inputs:
- options spread backtest data for trade ledger, equity curve, KPIs, and parameterized strategy runs.
- historical options fear-score data for historical entry filters.
- equity price history and implied-volatility history for underlying and volatility inputs.
- options strategy construction data and option position simulation data for spread pricing and payoff validation.

## Workflow

1. Define ticker, start/end date, target DTE, short delta, spread width, take-profit, stop-loss, and signal threshold.
2. Run signal-filtered strategy and no-signal control under identical parameters.
3. Compare annualized return, win rate, Sharpe, drawdown, trade count, and tail loss.
4. Inspect trade ledger and exit reasons before concluding signal quality.
5. Recommend parameter changes only after showing sensitivity.

## Output Format

1. **Backtest Verdict**: signal helps, hurts, or inconclusive.
2. **KPI Table**: signal vs control.
3. **Risk Table**: max drawdown, worst trade, loss streak, exposure.
4. **Trade Ledger Summary**: counts by exit reason.
5. **Data Used**.

## Guardrails

- Do not annualize from tiny sample sizes without warning.
- Do not compare strategies with different risk per trade.
- Clearly state whether historical option prices are observed or model-derived.
