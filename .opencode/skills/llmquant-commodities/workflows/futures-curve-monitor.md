# Futures Curve Monitor

## Use When

Use this workflow when the user asks whether a commodity futures curve is in contango or backwardation, how roll yield is changing, or what curve shifts imply for futures, ETFs, producers, or consumers.

## LLMQuant Data Needed

Required or future:
- commodity futures curve data: contract ladder, prices, maturities, volume, and open interest.
- historical commodity curve snapshots: historical curve snapshots for percentile and shift analysis.
- commodity spot or front-month market data: spot or front-month context.
- commodity inventory data: inventory pressure and release date.

Optional:
- equity price history
- ETF holdings data
- macro indicator snapshot data

Freshness:
- Report curve timestamp, contract months, front-month roll date, and inventory date.

Fallback:
- If curve history is unavailable, calculate only the current curve shape and label history-based conclusions as unavailable.

## Workflow

1. Define contract universe, benchmark months, and whether the user needs spot, futures, ETF, or equity implications.
2. Pull the current curve and available historical curve snapshots.
3. Calculate front-to-second spread, 3/6/12-month spreads, annualized roll yield, and curve percentile.
4. Link curve shape to inventory, macro, and seasonal evidence when available.
5. Translate the curve into implications for futures exposure, commodity ETFs, producers, and consumers.

## Output Format

1. **Curve State**
2. **Roll Yield**
3. **Curve Shift**
4. **Inventory / Macro Context**
5. **Implications**
6. **Data Used**

## Guardrails

- Do not estimate futures contracts without LLMQuant Data.
- Do not assume ETF performance equals spot commodity performance.
- Separate current curve math from historical percentile analysis.
