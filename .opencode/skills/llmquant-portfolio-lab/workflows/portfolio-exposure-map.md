# Portfolio Exposure Map

## Use When

Use this workflow when the user wants a map of portfolio exposure by holdings, sectors, factors, geography, market cap, ETF look-through, concentration, or risk contribution.

## LLMQuant Data Needed

Required or future:
- portfolio position data: holdings, weights, cost basis, asset type, and as-of date.
- portfolio factor exposure data: beta, size, value, momentum, quality, rates, FX, commodity, and sector exposures.
- portfolio risk model output: volatility, correlation, marginal contribution to risk, and drawdown contribution.
- equity price history: price history for listed holdings.
- ETF holdings data: ETF look-through holdings and weights.

Optional:
- option Greeks data
- crypto market snapshot data
- macro indicator snapshot data

Freshness:
- Report portfolio as-of date, price date, holdings as-of date for ETFs, and risk model date.

Fallback:
- If no portfolio API is available, ask for or build a holdings table with ticker, weight, quantity, asset type, and cost basis.

## Workflow

1. Normalize holdings, weights, identifiers, and asset types.
2. Pull price, ETF look-through, factor, sector, geography, and risk-model data.
3. Aggregate exposures at security, issuer, sector, factor, geography, and asset-class levels.
4. Identify concentration, hidden overlap, unintended factor bets, and top risk contributors.
5. Produce an exposure map and action-ready diagnostics.

## Output Format

1. **Portfolio Map**
2. **Concentration**
3. **Factor And Sector Exposure**
4. **ETF Look-Through**
5. **Risk Contributors**
6. **Data Used**

## Guardrails

- Do not invent holdings, weights, or factor exposures.
- Do not net exposures across unrelated instruments unless the workflow explicitly defines the rule.
- Clearly label unsupported asset types.
