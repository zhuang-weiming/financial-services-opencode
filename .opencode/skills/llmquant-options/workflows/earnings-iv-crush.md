---
name: Earnings IV Crush
description: Analyze earnings-related implied moves, IV crush history, straddle performance, and short-volatility setups using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Earnings IV Crush

## Purpose

Evaluate whether pre-earnings options are pricing too much, too little, or a fair move, and build a risk-defined earnings trade only when justified.

## Input Data Source

Use **LLMQuant Data** for earnings dates, historical IV crush, implied move, option chains, simulations, and historical price moves.

## Data Needed

Required LLMQuant Data inputs:
- equity event calendar data for next earnings date and timing.
- earnings implied-volatility data for pre/post earnings IV history, average crush, implied move, and actual move history.
- option chain data and implied-volatility snapshot data for current contracts and IV rank.
- option position simulation data for iron condor, straddle, strangle, or directional setups.
- equity price history for actual post-earnings moves.

## Workflow

1. Pull next earnings date and prior earnings events.
2. Compare current implied move to prior actual moves.
3. Evaluate IV rank, crush history, and straddle win/loss history.
4. Build candidate trade only if event timing and liquidity are adequate.
5. Present short-volatility and long-volatility cases separately.

## Output Format

1. **Earnings Verdict**: short IV, long IV, directional, or no trade.
2. **Implied Move**: percent, dollars, expiry, timestamp.
3. **History Table**: prior implied move, actual move, IV crush, straddle P&L.
4. **Candidate Structure**: legs, credit/debit, max loss, breakevens.
5. **Data Used**.

## Guardrails

- Do not recommend naked short options into earnings.
- Do not annualize event trades as if they are repeatable weekly yields.
- If earnings date is unconfirmed, mark the analysis provisional.
