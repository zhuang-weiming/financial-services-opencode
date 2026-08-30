# FX Carry Dashboard

## Use When

Use this workflow when the user asks for FX carry, dollar regime, currency ranking, carry trade risk, or hedging currency exposure.

## LLMQuant Data Needed

Required:
- FX spot history, volatility, drawdown, trend, and correlation data.
- short-rate differentials, yield curves, forward points, and carry estimates when available.
- inflation, growth, current account, commodity exposure, credit risk, and central-bank context.
- risk sentiment indicators such as equities, volatility, credit, funding stress, and liquidity.

Freshness:
- Report FX price timestamp, rate observation date, forward/carry timestamp, macro dates, and stale-data notices.

Fallback:
- If forward points are unavailable, use short-rate differentials as a carry proxy and label it clearly.

## Workflow

1. Define currency universe, base currency, hedge objective, and horizon.
2. Rank currencies by carry, momentum, volatility, valuation proxy, and macro quality.
3. Check whether carry is supported by risk sentiment or vulnerable to unwind.
4. Identify trade or hedge candidates with expected carry, volatility, and event risks.
5. Provide monitoring triggers for stop, hedge adjustment, or no-trade.

## Output Format

1. **FX Regime**
2. **Carry Dashboard**
3. **Momentum / Volatility**
4. **Macro Quality**
5. **Candidates And Risks**
6. **Data Used**

## Guardrails

- Do not call high carry attractive without volatility and drawdown checks.
- Do not confuse spot returns with hedged returns.
- Do not ignore intervention, capital controls, or event risk.
