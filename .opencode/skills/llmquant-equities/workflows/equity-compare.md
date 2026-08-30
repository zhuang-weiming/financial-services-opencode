---
name: Equity Compare
description: Compare 2-5 stocks or ETFs side by side across fundamentals, valuation, technicals, volatility, sentiment, and flow using LLMQuant Data.
input_data_source: LLMQuant Data
pack: research
---

# Equity Compare

## Purpose

Rank a small set of tickers by the dimensions that matter for the user's question: cheaper valuation, better quality, stronger momentum, lower risk, cleaner ownership, or more attractive volatility setup.

## Input Data Source

Use **LLMQuant Data** for all market, fundamental, options, ETF, and ownership evidence. Cite dates and coverage notices for every ticker.

## Data Needed

Required LLMQuant Data inputs:
- equity market snapshot data for price, market cap, sector, liquidity, and recent move.
- company fundamentals data and valuation multiple data for quality and valuation comparison.
- equity technical indicator data and equity price history for trend, drawdown, volatility, and relative strength.
- implied-volatility snapshot data for IV rank, IV percentile, historical volatility, and VRP when optionable.
- ticker-level 13F holder data for institutional sponsorship and crowding.
- ETF identity and profile lookup and ETF holdings data when the compared tickers are ETFs.

## Workflow

1. Accept 2-5 tickers and identify the comparison objective.
2. Pull the same evidence set for each ticker where coverage exists.
3. Normalize units and dates so comparisons are fair.
4. Rank each ticker by dimension and highlight category winners.
5. Produce an overall ranking only after explaining the weights used.

## Output Format

1. **Winner / Ranking**: overall ranking and weighting.
2. **Comparison Table**: price action, quality, valuation, technicals, volatility, flow.
3. **Category Winners**: best quality, cheapest valuation, best momentum, lowest risk.
4. **Decision Notes**: what would change the ranking.
5. **Data Used**: data capabilities, dates, missing fields, stale warnings.

## Guardrails

- Do not compare metrics retrieved on materially different dates without noting it.
- Do not force an overall winner when the user's objective is dimension-specific.
- For ETF comparisons, distinguish holdings overlap from price performance.
