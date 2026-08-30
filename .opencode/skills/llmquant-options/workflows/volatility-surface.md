---
name: Volatility Surface
description: Analyze implied volatility across strikes and expirations, including term structure, skew, and anomalies using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Volatility Surface

## Purpose

Map implied volatility by moneyness and expiry to understand whether options are cheap, expensive, event-distorted, skewed, or anomalous.

## Input Data Source

Use **LLMQuant Data** for options surface, chain, IV, spot, and event dates.

## Data Needed

Required LLMQuant Data inputs:
- volatility surface data for surface grid, moneyness axis, expiry axis, and fitted values.
- option chain data for raw IV, bid/ask, volume, and open interest.
- implied-volatility snapshot data for ATM IV, IV rank, HV, and VRP.
- equity market snapshot data and equity event calendar data for spot and event context.

## Workflow

1. Pull the surface across requested expiries and moneyness range.
2. Classify term structure as contango, flat, backwardated, or event-kinked.
3. Measure skew and identify deviations from fitted surface.
4. Connect surface shape to candidate strategies.
5. Flag anomalies that are untradeable due to spread or liquidity.

## Output Format

1. **Surface Verdict**: normal, backwardated, steep skew, event kink, anomaly.
2. **Term Structure**: ATM IV by expiry.
3. **Skew / Smile**: put-call skew by expiry.
4. **Anomalies**: contract, expected IV, actual IV, liquidity.
5. **Data Used**.

## Guardrails

- Do not call a surface point mispriced if bid/ask is wide or open interest is negligible.
- Distinguish fitted-surface anomalies from actual executable trades.
- Always report the surface timestamp.
