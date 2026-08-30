---
name: Volatility Smile
description: Analyze IV skew and smile shape for a single expiration using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Volatility Smile

## Purpose

Zoom into one expiration to evaluate put skew, call skew, smile shape, risk reversal, and whether one side of the chain is unusually expensive.

## Input Data Source

Use **LLMQuant Data** for smile data, chain liquidity, IV snapshot, spot, and events.

## Data Needed

Required LLMQuant Data inputs:
- volatility smile data for strike-level IV, delta, moneyness, risk reversal, and skew percentile.
- option chain data for liquidity and bid/ask validation.
- implied-volatility snapshot data for overall IV context.
- equity market snapshot data and equity event calendar data for spot and event timing.

## Workflow

1. Choose expiry, defaulting to the nearest liquid monthly expiry if unspecified.
2. Pull strike-level IV and liquidity.
3. Measure 25-delta skew, 10-delta skew, risk reversal, and shape.
4. Classify as normal, flat, reverse, winged, or event-driven.
5. Translate the skew into possible spread, hedge, or premium-sale implications.

## Output Format

1. **Smile Verdict**: shape, steepness, percentile, event context.
2. **Skew Metrics**: 25d skew, risk reversal, ATM IV, expiry.
3. **Strike Table**: selected strikes, IV, delta, bid/ask, OI.
4. **Trade Implications**: sell/buy skew, hedge cost, caution.
5. **Data Used**.

## Guardrails

- Do not infer market direction from skew alone.
- Do not use illiquid wing quotes as reliable skew signals.
- Keep expiry and DTE visible.
