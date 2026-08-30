# Probability Vs Options Pricing

## Use When

Use this workflow when the user asks how prediction-market odds compare with options-implied pricing, volatility markets, or event-window asset moves.

## LLMQuant Data Needed

Required:
- prediction-market contract odds, settlement criteria, liquidity, and timestamp.
- related equity, ETF, index, rate, FX, or crypto price history.
- option chain, implied volatility, skew, term structure, and event-window implied move data.
- event date, relevant announcement time, and post-event trading window.

Freshness:
- Report option quote time, prediction-market time, asset price time, and event calendar date.

Fallback:
- If option-chain data is unavailable, compare only to historical moves and say options-implied probability is missing.

## Workflow

1. Define the event and map it to tradable related assets.
2. Convert prediction-market odds into a probability range after liquidity and fees.
3. Estimate options-implied move or probability using the matching event window.
4. Compare probability spread, basis risk, liquidity, and payoff convexity.
5. Explain whether the gap is tradable, informational, or too basis-heavy.

## Output Format

1. **Probability Gap**
2. **Event-To-Asset Mapping**
3. **Options-Implied View**
4. **Basis Risk**
5. **Possible Expressions**
6. **Data Used**

## Guardrails

- Do not map a binary contract to an option payoff without explaining payoff mismatch.
- Do not use mismatched dates or expiries.
- Do not present a probability gap as a guaranteed trade.
