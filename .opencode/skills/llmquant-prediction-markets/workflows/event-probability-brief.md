# Event Probability Brief

## Use When

Use this workflow when the user asks for a probability view on an election, policy decision, macro release, court decision, sports-adjacent finance event, listing, approval, or other contract-defined outcome.

## LLMQuant Data Needed

Required:
- prediction-market contract definition, settlement criteria, closing time, outcome set, and venue.
- market odds, bid/ask, depth, volume, open interest, fees, and latest update timestamp.
- related evidence such as macro data, filings, news, polling, sector prices, or issuer context.
- historical event analogs when available.

Freshness:
- Report contract timestamp, event date, close date, evidence observation dates, and stale-data notices.

Fallback:
- If settlement criteria are missing or ambiguous, lead with that limitation and avoid a firm probability call.

## Workflow

1. Define the contract and rewrite the settlement rule in plain language.
2. Convert market price to probability after considering bid/ask, fees, and liquidity.
3. Gather evidence that can move the probability before settlement.
4. Compare market-implied probability with evidence-implied directional pressure.
5. Produce a probability range and identify triggers that would change it.

## Output Format

1. **Probability View**
2. **Contract Terms**
3. **Market Odds And Liquidity**
4. **Evidence For / Against**
5. **Catalysts And Monitors**
6. **Data Used**

## Guardrails

- Do not treat price as truth when liquidity is thin.
- Do not compare contracts with different settlement rules as equivalent.
- Do not give legal, political, or gambling advice.
