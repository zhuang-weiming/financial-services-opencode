# Regulatory Risk Monitor

## Use When

Use this workflow when the user asks about regulatory, legal, antitrust, FDA, policy, geopolitical, or compliance risk affecting a company, sector, asset, or event.

## LLMQuant Data Needed

Required:
- filings, risk factors, legal proceedings, company disclosures, regulatory calendars, and policy events.
- price history, volatility, options, sector peers, news, and sentiment around the affected asset.
- historical event analogs, regulatory decisions, and enforcement history when available.
- prediction-market or probability evidence when a contract-defined regulatory outcome exists.

Freshness:
- Report filing date, event date, regulatory calendar date, news timestamp, market price date, and stale-data notices.

Fallback:
- If regulatory docket or event calendar data is unavailable, frame the output as a risk map and list missing evidence.

## Workflow

1. Define the regulator, jurisdiction, asset, event, and decision window.
2. Summarize the rule, approval, lawsuit, investigation, or policy issue in plain language.
3. Link risk to revenue, cost, valuation, capital structure, supply chain, or license-to-operate exposure.
4. Compare market pricing, options, peers, and historical analogs where available.
5. Produce a monitor with trigger events, probability range, and scenario implications.

## Output Format

1. **Risk Summary**
2. **Exposure Map**
3. **Evidence Timeline**
4. **Market Pricing**
5. **Scenarios / Triggers**
6. **Data Used**

## Guardrails

- Do not give legal advice.
- Do not infer regulatory outcomes from political preference.
- Do not invent docket entries, agency statements, or decision dates.
