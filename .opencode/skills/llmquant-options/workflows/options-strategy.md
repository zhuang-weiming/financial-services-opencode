---
name: Options Strategy Builder
description: Select and build multi-leg option strategies for bullish, bearish, neutral, income, hedge, or volatility views using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Options Strategy Builder

## Purpose

Translate a market view into a concrete options structure with strikes, expiries, cost/credit, breakevens, max profit/loss, probability, and risk notes.

## Input Data Source

Use **LLMQuant Data** for strategy templates, chains, IV, Greeks, simulation, and underlying data.

## Data Needed

Required LLMQuant Data inputs:
- options strategy template data for supported structures and rules.
- options strategy construction data for leg construction from a template.
- option chain data, implied-volatility snapshot data, and option Greeks data for contract selection.
- option position simulation data for payoff, probability, and scenarios.
- equity market snapshot data for underlying price and liquidity.

Supported views:
- Bullish: long call, bull call spread, bull put spread, synthetic long.
- Bearish: long put, bear put spread, bear call spread, synthetic short.
- Neutral/income: covered call, cash-secured put, iron condor, short strangle, calendar.
- Volatile: straddle, strangle, reverse iron condor.
- Hedge: protective put, collar, put spread collar.

## Workflow

1. Clarify view, timeframe, max loss, income versus convexity, and account constraints.
2. Pull IV environment and option chain.
3. Choose candidate templates that fit the view and IV regime.
4. Build top 1-3 structures and simulate P&L.
5. Recommend one primary structure and show alternatives.

## Output Format

1. **Strategy Recommendation**: structure, why it fits, confidence.
2. **Leg Table**: action, call/put, strike, expiry, price, IV, delta.
3. **Payoff**: max profit/loss, breakevens, probability, margin/capital.
4. **Scenarios**: price move, IV shock, time decay.
5. **Data Used**.

## Guardrails

- Do not recommend undefined-risk strategies unless the user explicitly allows them.
- Do not assume margin eligibility.
- Always include max loss or clearly state if loss is theoretically unlimited.
