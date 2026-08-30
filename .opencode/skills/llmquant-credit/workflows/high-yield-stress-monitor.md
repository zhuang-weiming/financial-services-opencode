# High Yield Stress Monitor

## Use When

Use this workflow when the user asks about high-yield stress, refinancing risk, fallen angels, default pressure, or credit-market contagion.

## LLMQuant Data Needed

Required:
- high-yield spreads, distressed ratios, default rates, rating migration, and sector spread dispersion when available.
- maturity walls, refinancing calendar, issuer fundamentals, and debt-service burden.
- high-yield ETF prices, discounts, flows, holdings, and liquidity context.
- macro indicators, rates, equity drawdowns, volatility, commodity prices, and bank stress indicators.

Freshness:
- Report spread date, rating date, issuer filing date, ETF holdings date, and macro observation dates.

Fallback:
- If distressed ratios or default data are unavailable, produce a proxy stress monitor and list missing credit inputs.

## Workflow

1. Define high-yield universe, sector focus, and risk horizon.
2. Check market stress: spreads, dispersion, ETF discounts, liquidity, and equity drawdowns.
3. Check fundamental stress: leverage, coverage, free cash flow, maturity wall, and downgrade risk.
4. Identify vulnerable sectors and issuers.
5. Map stress level to portfolio actions and monitoring triggers.

## Output Format

1. **Stress Level**
2. **Market Stress**
3. **Fundamental Stress**
4. **Vulnerable Segments**
5. **Triggers / Hedges**
6. **Data Used**

## Guardrails

- Do not infer default risk from price declines alone.
- Do not ignore refinancing calendar and rate environment.
- Distinguish market liquidity stress from issuer solvency stress.
