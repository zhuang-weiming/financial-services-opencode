---
name: Five-Lens Stock Analysis
description: Analyze a public equity through fundamentals, valuation, technicals, sentiment, and ownership flow using LLMQuant Data.
input_data_source: LLMQuant Data
pack: research
---

# Five-Lens Stock Analysis

## Purpose

Produce a dated, evidence-first stock view with a composite score, recommendation range, risk flags, target/stop framework, and the data used.

## Input Data Source

Use **LLMQuant Data** as the input data source for prices, fundamentals, valuation, technicals, filings, institutional ownership, and market sentiment. State returned dates, filing periods, observation dates, and stale-data notices.

## Data Needed

Required LLMQuant Data inputs:
- equity market snapshot data for current price, market cap, sector, volume, and 52-week range.
- company fundamentals data for revenue growth, margins, ROE, leverage, FCF, dividends, and analyst estimates if available.
- valuation multiple data for PE, forward PE, PEG, EV/EBITDA, FCF yield, price/sales, and peer percentiles.
- equity technical indicator data and equity price history for trend, moving averages, RSI, ATR, drawdown, and volatility.
- SEC filing discovery and SEC filing section retrieval for latest 10-K/10-Q business, MD&A, and risk evidence.
- ticker-level 13F holder data for sponsorship, concentration, and manager crowding.
- market sentiment snapshot data for VIX, breadth, put/call, and sector rotation context.

## Scoring Model

Score each lens from 0-10:
- Fundamentals: growth quality, margin durability, balance sheet, FCF conversion.
- Valuation: absolute multiples, peer-relative multiples, FCF yield versus rates, historical band.
- Technicals: trend, momentum, support/resistance, ATR risk.
- Sentiment: market regime, sector sentiment, news/event pressure, volatility backdrop.
- Flow: 13F sponsorship, concentration, ownership changes, unusual activity if available.

Recommendation bands:
- 8.0-10.0: Strong bullish candidate, subject to risk controls.
- 6.5-7.9: Bullish/watchlist, needs price or catalyst confirmation.
- 4.0-6.4: Neutral or mixed.
- 2.5-3.9: Avoid or reduce.
- 0-2.4: High-risk avoid unless explicitly hedged.

## Workflow

1. Normalize the ticker and identify exchange/asset coverage.
2. Pull snapshot, fundamentals, valuation, price history, technicals, filings, 13F, and sentiment.
3. Check freshness and missing fields before scoring.
4. Score the five lenses and explain the strongest positive and negative drivers.
5. Build a target/stop framework using valuation upside, ATR downside, and thesis-break risks.
6. Separate facts from interpretation and include a data-used block.

## Output Format

1. **Recommendation**: rating, composite score, confidence, target range, stop/risk level.
2. **Five-Lens Table**: score, key evidence, data date for each lens.
3. **Bull Case / Bear Case**: concise evidence-based arguments.
4. **Risk Controls**: stop-loss logic, position sizing hint, thesis-break triggers.
5. **Data Used**: data capabilities, dates, filing periods, coverage caveats.

## Guardrails

- Do not fill missing financial metrics from memory.
- Do not imply current fundamentals if only historical filings were retrieved.
- Do not present a score without showing the evidence driving it.
- If the ticker is unsupported, state the missing coverage and provide only a framework.
