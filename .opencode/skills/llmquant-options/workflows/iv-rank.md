---
name: Options IV Rank
description: Evaluate whether a ticker's implied volatility is cheap or expensive versus its own history using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Options IV Rank

## Purpose

Place current implied volatility in historical context and decide whether the volatility environment favors buying premium, selling premium, or waiting.

## Input Data Source

Use **LLMQuant Data** for implied volatility, historical volatility, optionable ticker coverage, event dates, and price history.

## Data Needed

Required LLMQuant Data inputs:
- implied-volatility snapshot data for ATM IV, IV rank, IV percentile, HV, VRP, and timestamp.
- implied-volatility history for 252-trading-day IV and HV history.
- equity price history for realized volatility, drawdown, and gaps.
- equity event calendar data for earnings and event-driven IV spikes.

## Workflow

1. Pull current IV snapshot and 1-year IV history.
2. Calculate or verify IV rank, IV percentile, HV/IV ratio, and VRP.
3. Check for upcoming earnings or corporate events that distort IV.
4. Classify volatility as very low, low, neutral, high, or very high.
5. Map the IV zone to strategy bias: long premium, debit spreads, neutral, credit spreads, or avoid.

## Output Format

1. **IV Verdict**: cheap, fair, expensive, or event-distorted.
2. **Metrics**: current IV, IV rank, IV percentile, HV, VRP, date.
3. **History Context**: 52-week high/low/mean and notable spikes.
4. **Strategy Bias**: buy/sell premium with caveats.
5. **Data Used**.

## Guardrails

- Do not recommend selling premium solely because IV rank is high; check event risk.
- Do not compare IV rank across tickers as if distributions are identical.
- Report if IV history is shorter than the requested lookback.
