# Earnings Event Brief

## Use When

Use this workflow when the user asks for an earnings preview, post-earnings read, implied move check, setup, or catalyst risk for a company.

## LLMQuant Data Needed

Required:
- earnings date, company profile, filings, prior results, segment context, and management guidance.
- price history, volume, realized volatility, drawdowns, sector and peer returns.
- estimates, revisions, surprises, margins, revenue drivers, and valuation context when available.
- options-implied move, implied volatility, skew, open interest, and event-window history when available.

Freshness:
- Report earnings date, estimate timestamp, option quote time, filing date, and price window.

Fallback:
- If estimates or options are unavailable, produce a fundamentals-and-price setup only and list missing inputs.

## Workflow

1. Define the company, reporting period, event date, and investor horizon.
2. Summarize expectations: revenue, margins, guidance, key metrics, and sell-side revision trend.
3. Analyze setup: price trend, valuation, positioning, sentiment, peers, and options-implied move.
4. Build upside, base, and downside scenarios with evidence thresholds.
5. Translate the setup into watch items and post-event interpretation rules.

## Output Format

1. **Event Setup**
2. **Expectations**
3. **Options / Positioning**
4. **Scenario Table**
5. **Post-Event Checklist**
6. **Data Used**

## Guardrails

- Do not invent estimates or guidance.
- Do not equate implied move with probability of direction.
- Separate pre-event setup from post-event conclusion.
