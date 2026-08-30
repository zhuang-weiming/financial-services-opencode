---
name: Unusual Options Activity
description: Detect and interpret unusual options flow, block trades, sweeps, volume/OI spikes, and premium imbalance using LLMQuant Data.
input_data_source: LLMQuant Data
pack: trading
---

# Unusual Options Activity

## Purpose

Surface notable option trades and decide whether they are directional, hedging, event-driven, liquidity noise, or non-actionable.

## Input Data Source

Use **LLMQuant Data** for unusual activity, flow summaries, option chains, underlying prices, and event context.

## Data Needed

Required LLMQuant Data inputs:
- unusual options activity data for trade-level timestamp, contract, size, premium, side, venue, and classification.
- options flow summary data for net call/put premium, sector flow, and historical signal quality.
- option chain data for OI, volume, bid/ask, IV, and contract metadata.
- equity market snapshot data and equity event calendar data for price move and catalyst context.

## Workflow

1. Pull ticker-specific or market-wide unusual activity.
2. Filter by premium, volume/open-interest ratio, urgency, and liquidity.
3. Classify each signal as bullish, bearish, hedge, roll, earnings, or unclear.
4. Compare flow to price action and upcoming events.
5. Present only signals with enough context to interpret.

## Output Format

1. **Flow Summary**: net premium, smart-money score, sentiment.
2. **Top Trades**: timestamp, contract, premium, vol/OI, classification.
3. **Interpretation**: directional or hedge, evidence, confidence.
4. **Risks**: late print, spread trade, hedge, event distortion.
5. **Data Used**.

## Guardrails

- Do not call every large trade bullish or bearish; hedges and rolls are common.
- Do not infer buyer/seller side unless the data supports it.
- Report timestamp and liquidity.
