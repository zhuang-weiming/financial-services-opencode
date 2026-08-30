# Crypto Market Regime

## Use When

Use this workflow when the user asks whether crypto is risk-on, risk-off, levered, range-bound, capitulating, or entering a new market regime.

## LLMQuant Data Needed

Required:
- crypto price and volume history for BTC, ETH, major tokens, and the requested benchmark universe.
- realized volatility, drawdown, momentum, correlation, and market breadth data for regime scoring.
- crypto liquidity data such as stablecoin supply, exchange liquidity, ETF flows, or venue depth when available.
- perpetual funding, basis, open interest, and liquidation data for leverage and crowding context.
- macro and cross-asset context such as rates, dollar, liquidity, equities, gold, and risk indicators.

Freshness:
- Report price window, venue timestamp, funding interval, macro observation dates, and stale-data notices.

Fallback:
- If leverage or liquidity data is unavailable, classify only the price/macro regime and list the missing inputs.

## Workflow

1. Define the universe, benchmark, horizon, and decision lens: allocation, hedge, trade, or risk review.
2. Measure trend, breadth, realized volatility, drawdown, and correlation versus macro assets.
3. Check leverage conditions using funding, basis, open interest, and liquidation evidence.
4. Add liquidity and macro context, including stablecoins, dollar, rates, and risk appetite.
5. Classify the regime and map it to actions: accumulate, hold, hedge, reduce, or wait.

## Output Format

1. **Regime Call**
2. **Market Dashboard**
3. **Leverage / Liquidity**
4. **Macro Linkage**
5. **Scenario Triggers**
6. **Data Used**

## Guardrails

- Do not claim live market state without timestamped data.
- Do not treat one exchange or one token as the whole market.
- Separate regime evidence from trade recommendations.
