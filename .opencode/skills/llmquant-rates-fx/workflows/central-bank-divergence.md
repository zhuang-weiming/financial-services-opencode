# Central Bank Divergence

## Use When

Use this workflow when the user asks how Fed, ECB, BOJ, BOE, PBOC, or other central-bank paths differ and how that affects rates, FX, equities, commodities, and credit.

## LLMQuant Data Needed

Required:
- policy rates, meeting calendars, policy communication, inflation, labor, growth, and financial conditions by country.
- yield curves, real rates, rate differentials, FX spot history, and volatility.
- market-implied policy path and forward-rate context when available.
- commodity, equity, credit, and liquidity data relevant to country divergence.

Freshness:
- Report policy date, meeting date, macro observation dates, rate and FX price dates, and stale-data notices.

Fallback:
- If market-implied policy path is unavailable, compare realized policy rates and macro data only.

## Workflow

1. Define countries, central banks, horizon, and assets affected.
2. Compare inflation, growth, labor, financial conditions, and policy stance.
3. Measure rate differentials, real-rate differentials, and FX response.
4. Identify where markets are priced for convergence or divergence.
5. Produce asset implications and triggers for regime change.

## Output Format

1. **Divergence Thesis**
2. **Policy / Macro Table**
3. **Rates And FX Pricing**
4. **Asset Implications**
5. **Triggers**
6. **Data Used**

## Guardrails

- Do not treat central banks as interchangeable.
- Do not ignore capital controls, intervention risk, or commodity exposure.
- Distinguish macro divergence from market pricing divergence.
