# Commodity Market Lens

## Use When

Use this workflow when the user asks for a commodity market brief, commodity regime read, or supply/demand view for oil, gas, gold, copper, agricultural commodities, or another commodity complex.

## LLMQuant Data Needed

Required or future:
- commodity spot or front-month market data: spot price, recent change, volume, and observation timestamp.
- commodity futures curve data: active futures contracts, maturities, prices, curve shape, and roll yield.
- commodity inventory data: inventory levels, draws/builds, and regional storage data.
- commodity production and demand data: production, demand, export/import, and utilization series.
- macro indicator snapshot data and macro indicator history: rates, USD, inflation, growth, and energy indicators.
- equity price history: related producer, consumer, or ETF proxies.

Optional:
- commodity news and event context
- weather risk data
- geopolitical event context

Freshness:
- Report observation dates, contract dates, inventory release dates, and stale-data notices.

Fallback:
- If commodity endpoints are unavailable, name the missing LLMQuant Data inputs and continue only with available macro, price-proxy, or equity evidence.

## Workflow

1. Define commodity, geography, benchmark contract, horizon, and decision context.
2. Pull spot, futures curve, inventory, production/demand, macro, FX, and related equity/ETF data.
3. Classify price trend, curve shape, inventory pressure, macro tailwind/headwind, and event risk.
4. Separate structural signals from short-term positioning or event noise.
5. Produce a data-grounded market lens with scenarios.

## Output Format

1. **Commodity View**
2. **Price And Curve**
3. **Supply / Demand**
4. **Macro Linkage**
5. **Related Equity Or ETF Read-Through**
6. **Scenarios**
7. **Data Used**

## Guardrails

- Do not infer current spot prices, inventories, or curve shape without LLMQuant Data.
- Do not treat commodity ETFs as perfect spot exposure unless holdings and roll mechanics are checked.
- Do not make personalized trading advice claims.
