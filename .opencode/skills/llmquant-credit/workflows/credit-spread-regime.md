# Credit Spread Regime

## Use When

Use this workflow when the user asks whether credit spreads are tight, wide, widening, complacent, stressed, or signaling recession risk.

## LLMQuant Data Needed

Required:
- investment-grade, high-yield, leveraged-loan, CDS, sector, and rating-bucket spread data when available.
- rates, yield curves, real rates, inflation, growth, unemployment, liquidity, and financial conditions data.
- equity index, volatility, bank, small-cap, commodity, and FX market data.
- credit ETF prices, flows, discounts, and holdings when available.

Freshness:
- Report spread date, market price date, macro observation dates, and stale-data notices.

Fallback:
- If spread histories are unavailable, use ETF, equity, rates, and macro proxies and label the analysis as proxy-based.

## Workflow

1. Define region, credit universe, rating bucket, and horizon.
2. Measure current spread level, change, percentile, and curve shape where data exists.
3. Compare spreads with macro, rates, equity volatility, liquidity, and default-cycle evidence.
4. Identify sectors or rating buckets carrying the stress.
5. Translate the regime into risk posture: add, hold, hedge, reduce, or wait.

## Output Format

1. **Spread Regime**
2. **Credit Dashboard**
3. **Macro Confirmation**
4. **Sector / Rating Stress**
5. **Portfolio Implications**
6. **Data Used**

## Guardrails

- Do not call spreads tight or wide without a reference window.
- Do not use price-only proxies as true spreads without disclosure.
- Do not ignore duration when comparing credit instruments.
