# Yield Curve Trade Lens

## Use When

Use this workflow when the user asks about duration, steepeners, flatteners, curve inversion, real rates, bond ETFs, or yield-curve signals.

## LLMQuant Data Needed

Required:
- yield curve observations across relevant tenors, histories, and curve spreads.
- policy rate, inflation, inflation expectations, growth, labor, and liquidity indicators.
- bond ETF prices, duration, holdings, and rate-sensitive equity or credit proxies when relevant.
- volatility, credit spreads, dollar, commodity, and equity market context.

Freshness:
- Report curve date, tenor set, macro observation dates, ETF holdings date, and stale-data notices.

Fallback:
- If duration or ETF holdings are unavailable, analyze curve shape and macro context without instrument-level exposure.

## Workflow

1. Define currency, tenors, instrument proxy, and trade horizon.
2. Measure curve level, slope, curvature, real-rate context, and recent shifts.
3. Compare curve signals with policy, inflation, growth, liquidity, and credit evidence.
4. Evaluate trade expressions such as duration, steepener, flattener, ETF, or hedge.
5. State invalidation levels, carry/roll considerations, and event risks.

## Output Format

1. **Curve View**
2. **Rate Dashboard**
3. **Macro Drivers**
4. **Trade Expressions**
5. **Risks / Invalidation**
6. **Data Used**

## Guardrails

- Do not recommend a curve trade without tenor, horizon, and carry/roll caveats.
- Do not compare nominal rates across countries without inflation and FX context.
- Do not infer ETF duration without data.
