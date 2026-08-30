# Portfolio What-If Simulator

## Use When

Use this workflow when the user wants to simulate adding, trimming, replacing, hedging, or shocking a portfolio before making a change.

## LLMQuant Data Needed

Required or future:
- portfolio position data: current holdings, weights, quantities, and cost basis.
- portfolio scenario simulation data: shock definitions, scenario returns, and portfolio impact.
- portfolio risk model output: volatility, beta, factor exposure, drawdown, and correlation.
- equity price history: historical returns for current and proposed holdings.
- ETF holdings data: look-through exposure for ETF adds or replacements.

Optional:
- option chain data
- option Greeks data
- macro indicator history

Freshness:
- Report portfolio as-of date, scenario date, price window, and model version/date.

Fallback:
- If simulation tooling is unavailable, produce a structured what-if input table and qualitative data-limited analysis.

## Workflow

1. Capture current portfolio and proposed change set.
2. Pull current exposure, risk, prices, and look-through data.
3. Build the pro forma portfolio after adds, trims, replacements, hedges, or shocks.
4. Compare current versus pro forma exposure, risk, drawdown, liquidity, and concentration.
5. Summarize what improved, what worsened, and what data remains missing.

## Output Format

1. **Pro Forma Summary**
2. **Current vs What-If Table**
3. **Risk And Exposure Changes**
4. **Scenario Outcomes**
5. **Implementation Caveats**
6. **Data Used**

## Guardrails

- Do not invent scenario returns or factor exposures.
- Do not treat a simulation as a forecast.
- Clearly separate user-provided assumptions from LLMQuant Data outputs.
