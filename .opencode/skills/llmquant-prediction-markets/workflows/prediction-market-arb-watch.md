# Prediction Market Arb Watch

## Use When

Use this workflow when the user asks whether two or more prediction-market contracts create an arbitrage, synthetic spread, or mispricing.

## LLMQuant Data Needed

Required:
- contract definitions, settlement criteria, outcome sets, deadlines, and venue rules.
- bid/ask, depth, volume, fees, withdrawal costs, and position limits.
- cross-venue prices and timestamps.
- related event evidence and market-impact context.

Freshness:
- Report the timestamp for each venue, each order-book snapshot, and any stale venue.

Fallback:
- If depth, fees, or settlement criteria are unavailable, label the result as a probability spread, not arbitrage.

## Workflow

1. Normalize contracts by event, outcome, deadline, and settlement authority.
2. Check whether outcomes are mutually exclusive, collectively exhaustive, or only partially overlapping.
3. Calculate gross spread, fee-adjusted spread, slippage sensitivity, and capital lockup.
4. Test basis risk: settlement mismatch, timing mismatch, venue risk, and ambiguous resolution.
5. Classify the setup as no arb, informational spread, conditional hedge, or executable only with missing-risk caveats.

## Output Format

1. **Arb Classification**
2. **Contract Mapping**
3. **Spread Math**
4. **Execution Constraints**
5. **Basis Risks**
6. **Data Used**

## Guardrails

- Do not call an opportunity arbitrage unless settlement, fees, depth, and timing all match.
- Do not ignore venue custody, withdrawal, and resolution risk.
- Do not assume order-book depth is executable after the query timestamp.
