# Crypto Perp Funding Monitor

## Use When

Use this workflow when the user asks about perpetual funding, basis trades, leverage crowding, short squeezes, long squeezes, or carry conditions in crypto.

## LLMQuant Data Needed

Required:
- perpetual funding rates by venue, asset, and interval.
- spot and perpetual prices for basis and annualized carry calculations.
- open interest, volume, liquidation, borrow, and margin-stress data when available.
- spot liquidity, exchange depth, and cross-venue price dispersion.
- macro and event context that can change funding or basis.

Freshness:
- Report venue, timestamp, funding interval, contract type, and calculation window.

Fallback:
- If open interest or liquidation data is unavailable, provide funding and basis only and avoid squeeze-probability claims.

## Workflow

1. Define assets, venues, contract types, and whether the user needs monitoring or a trade review.
2. Pull funding, spot, perp, basis, open interest, and liquidation evidence.
3. Calculate current funding, annualized carry, basis, and recent percentile where history exists.
4. Interpret whether the market is one-sided, balanced, or stressed.
5. Explain possible expressions and failure modes, including fees, slippage, venue risk, and liquidation risk.

## Output Format

1. **Funding State**
2. **Basis / Carry**
3. **Crowding And Stress**
4. **Possible Expressions**
5. **Failure Modes**
6. **Data Used**

## Guardrails

- Do not call a funding trade market-neutral without borrow, margin, liquidation, and venue-risk checks.
- Do not annualize stale or mismatched funding intervals.
- Do not compare venues without noting contract specifications.
