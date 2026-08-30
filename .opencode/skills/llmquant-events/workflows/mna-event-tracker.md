# M&A Event Tracker

## Use When

Use this workflow when the user asks about merger arbitrage, acquisition probability, deal spread, approvals, financing risk, shareholder votes, or break risk.

## LLMQuant Data Needed

Required:
- transaction announcement, deal terms, consideration type, price, spread, expected close, and termination provisions.
- filings, proxy statements, merger agreements, financing disclosures, and shareholder vote dates.
- target and acquirer price history, volatility, options, borrow, sector peers, and market context.
- regulatory approval milestones, antitrust jurisdictions, legal challenges, and news updates when available.

Freshness:
- Report deal announcement date, filing date, spread date, vote date, regulatory milestone date, and stale-data notices.

Fallback:
- If definitive agreement or spread data is unavailable, provide a deal timeline and missing-input list without probability scoring.

## Workflow

1. Identify target, acquirer, consideration, expected close date, and investor objective.
2. Build the deal timeline and unresolved conditions.
3. Calculate spread and implied return when current prices and terms are available.
4. Assess break risk: financing, antitrust, shareholder, legal, macro, and acquirer-stock risk.
5. Produce milestone tracker, probability range, and next evidence to monitor.

## Output Format

1. **Deal Snapshot**
2. **Spread / Return**
3. **Milestones**
4. **Break-Risk Map**
5. **Probability / Monitors**
6. **Data Used**

## Guardrails

- Do not compute deal spread without current price and consideration terms.
- Do not call a deal likely without addressing approvals and financing.
- Do not invent legal or regulatory deadlines.
