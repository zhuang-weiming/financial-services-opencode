---
name: Options P&L Simulator
description: Simulate P&L, breakevens, probability, and stress scenarios for single- or multi-leg option positions using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Options P&L Simulator

## Purpose

Show how an options position behaves across price, IV, and time, including expiry payoff, mark-to-market scenarios, probability of profit, and tail losses.

## Input Data Source

Use **LLMQuant Data** for option pricing, chain data, IV, Greeks, historical volatility, and simulation.

## Data Needed

Required LLMQuant Data inputs:
- option position simulation data for payoff grids, scenarios, probability, and Monte Carlo.
- option chain data for leg prices and contract details.
- option Greeks data and implied-volatility snapshot data for sensitivity context.
- equity market snapshot data and equity price history for spot and realized volatility.

## Workflow

1. Parse legs, quantities, entry prices, expiries, and scenario parameters.
2. Pull chain and IV data when live prices are needed.
3. Simulate expiry payoff and pre-expiry mark-to-market.
4. Run requested shocks: price, IV, time, gap, or event.
5. Present breakevens and max loss before expected profit.

## Output Format

1. **Position Summary**: legs, net debit/credit, capital at risk.
2. **Payoff**: max profit/loss, breakevens, probability.
3. **Scenario Table**: price down/up, IV crush/spike, time decay.
4. **Risk Flags**: tail loss, assignment, liquidity, event risk.
5. **Data Used**.

## Guardrails

- Do not simulate without clear long/short direction and quantity.
- If entry prices are missing, say whether live mid prices are used.
- Do not present Monte Carlo outputs without volatility and distribution assumptions.
