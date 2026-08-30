---
name: Options Score
description: Score and rank option contracts by liquidity, volatility value, Greeks balance, probability, and risk/reward using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Options Score

## Purpose

Find the best contracts for buy calls, buy puts, sell puts, and sell calls by ranking the option chain with transparent factors.

## Input Data Source

Use **LLMQuant Data** for option chains, expirations, prices, IV, Greeks, liquidity, technical levels, and underlying snapshots.

## Data Needed

Required LLMQuant Data inputs:
- option expiration data for available expiries.
- option chain data for bid/ask, last, volume, open interest, IV, strike, expiry, and contract id.
- option Greeks data for delta, gamma, theta, vega, rho, and probability metrics.
- implied-volatility snapshot data for IV rank and VRP.
- equity market snapshot data and equity technical indicator data for trend, ATR, support, and resistance.

## Scoring Factors

Score contracts from 0-100:
- Liquidity: volume, open interest, bid/ask width.
- Volatility value: IV rank, VRP, surface relative value.
- Greeks fit: delta, theta, vega, gamma for the intended strategy.
- Risk/reward: max loss, premium yield, breakeven, probability of profit.
- Technical alignment: support/resistance, trend, ATR buffer.

## Workflow

1. Identify strategy type, expiry, risk tolerance, and ticker.
2. Pull expirations, option chain, IV snapshot, Greeks, and technicals.
3. Score each contract with factor breakdowns.
4. Rank top candidates and explain why the winner scored well.
5. Flag illiquid, event-risk, or wide-spread contracts.

## Output Format

1. **Top Contracts**: ranked table with score and strategy.
2. **Score Breakdown**: factors and weights.
3. **Risk Notes**: liquidity, event, assignment, gap, margin.
4. **Next Step**: build strategy, simulate P&L, check Greeks.
5. **Data Used**.

## Guardrails

- Do not score stale or zero-liquidity contracts as tradeable.
- Do not hide assignment risk for short options.
- Do not rank contracts without showing bid/ask and open interest.
