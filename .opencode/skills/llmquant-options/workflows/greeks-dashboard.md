---
name: Greeks Dashboard
description: Calculate and interpret first- and second-order Greeks for single options or multi-leg positions using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Greeks Dashboard

## Purpose

Explain how an option or options position reacts to price, time, volatility, and rates, and identify the dominant risk exposures.

## Input Data Source

Use **LLMQuant Data** for option chains, IV, Greeks, rates, and underlying price.

## Data Needed

Required LLMQuant Data inputs:
- option Greeks data for contract-level delta, gamma, theta, vega, rho, charm, vanna, and volga.
- position-level Greeks data for multi-leg aggregation.
- implied-volatility calculation data when IV must be solved from market price.
- option chain data for tradable contract terms.
- equity market snapshot data and rates snapshot data for spot and risk-free assumptions.

## Workflow

1. Parse the position or contract definition.
2. Pull chain, IV, and Greeks; solve IV when needed.
3. Aggregate Greeks across legs and quantities.
4. Identify the largest risk: delta, gamma, theta, vega, or skew.
5. Run simple scenario checks if the user asks "what happens if".

## Output Format

1. **Net Exposure**: delta, gamma, theta, vega, rho.
2. **Per-Leg Table**: quantity, price, IV, Greeks.
3. **Risk Interpretation**: main sensitivity and what would hurt/help.
4. **Scenario Notes**: price, IV, time, rate shocks.
5. **Data Used**.

## Guardrails

- Do not aggregate Greeks without leg quantity and direction.
- State whether Greeks are per share, per contract, or total position.
- Report pricing assumptions: spot, IV, days to expiry, and rate.
