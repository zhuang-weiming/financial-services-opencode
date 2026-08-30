# Issuer Credit Risk Review

## Use When

Use this workflow when the user asks whether a company, issuer, bond, loan, or credit-sensitive equity has elevated credit risk.

## LLMQuant Data Needed

Required:
- issuer filings, financial statements, MD&A, risk factors, liquidity disclosures, and debt footnotes.
- debt maturity schedule, interest expense, cash, revolver capacity, covenant terms, ratings, and refinancing events.
- bond prices, spreads, CDS, rating history, and credit ETF context when available.
- equity price history, volatility, short interest, sector peers, rates, and macro context.

Freshness:
- Report filing period, filing date, market price date, rating date, and stale-data notices.

Fallback:
- If debt schedule or covenant terms are unavailable, avoid covenant headroom math and list the missing terms.

## Workflow

1. Identify issuer, securities, capital-structure layer, and time horizon.
2. Build the credit snapshot: leverage, coverage, liquidity, free cash flow, and maturity wall.
3. Compare market signals: spreads, CDS, equity drawdown, volatility, and sector pressure.
4. Review catalysts: refinancing, downgrade, covenant test, earnings, commodity or FX sensitivity.
5. Classify risk as improving, stable, watch, stressed, or distressed with evidence.

## Output Format

1. **Credit Verdict**
2. **Balance-Sheet Snapshot**
3. **Maturity / Liquidity**
4. **Market Signals**
5. **Catalysts And Watch Items**
6. **Data Used**

## Guardrails

- Do not infer debt terms from ticker memory.
- Do not treat equity upside as credit safety.
- Label absent bond, CDS, rating, or covenant data as missing.
