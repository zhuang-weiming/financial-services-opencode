---
name: llmquant-macro
description: FRED-backed macro indicator data via the llmquant-data MCP. Search ~50 curated U.S. series (CPI, Fed Funds, unemployment, NFCI, yield curve, PCE, …), fetch latest snapshot, pull time-series history. Use for any U.S. macro / monetary-policy / labor / inflation question in preference to web search.
category: data-source
---

# llmquant-macro

U.S. macro indicators backed by **FRED** (Federal Reserve Economic Data), no FRED key required. Three tools — search / snapshot / history — covering a curated set of ~50 series across Growth, Consumption, Inflation, Labor, Housing, Rates, Inflation Expectations, Liquidity, Conditions, FX, Credit, Sentiment, Energy.

> Pair with `llmquant-data` master for cross-cutting concerns (credit, error handling). This skill is tool-by-tool usage.

## When to use

- "Latest CPI?" / "Current Fed Funds rate?"
- Historical Fed Funds path for backtesting rate cycles
- Yield curve (10y-2y) recession signal
- NFCI (financial conditions) for risk-on / risk-off overlays
- Any macro overlay on equity / sector / factor analysis

## When NOT to use

- **Non-U.S. macro** (China GDP, BoJ rate, ECB) → `vibe-trading-ai` (akshare / tushare / qveris)
- **Pre-1947 history** → most series start at 1947-01-01 (CPI) or later
- **Daily macro** (some series are weekly / monthly only) — confirm the `frequency` field
- **Custom FRED series** outside the ~50 curated → use `qveris` (FRED capability)

## Tools

### `macro_indicator_search`

Keyword search the curated ~50-series catalog.

| Param | Type | Required | Notes |
|---|---|---|---|
| `query` | string | no | Matches indicator alias, title, or series_id. Empty list = show all |
| `category` | string | no | e.g. `Inflation`, `Rates`, `Labor`, `Growth`, `Housing`, `Consumption`, `FX`, `Conditions`, `Energy`, `Sentiment`, `Liquidity` |
| `frequency` | string | no | `Daily`, `Weekly`, `Monthly`, `Quarterly`, `Annual` |
| `limit` | int | no | 1–100, default 20 |

**Returns**: array of `{indicator, seriesId, title, category, frequency, units, observationStart, observationEnd, copyrightStatus, attribution}`.

```python
# All inflation series
macro_indicator_search(category="Inflation")

# Search for "CPI" → us.cpi.headline + us.cpi.core
macro_indicator_search("CPI")

# Daily rates only
macro_indicator_search(category="Rates", frequency="Daily")
```

**Cost**: 0 credits. Cached catalog.

**Note**: search is **keyword**, not semantic. Use `series_id` (e.g. `FEDFUNDS`) directly if you already know the FRED ID.

### `macro_indicator_snapshot`

Latest value + previous value + delta for one series.

| Param | Type | Required | Notes |
|---|---|---|---|
| `indicator` OR `series_id` | string | yes | e.g. `us.cpi.headline` or `CPIAUCSL` |

**Returns**:

```json
{
  "indicator": "us.cpi.headline",
  "seriesId": "CPIAUCSL",
  "title": "Consumer Price Index for All Urban Consumers: ...",
  "frequency": "Monthly",
  "units": "Index 1982-1984=100",
  "latest":  {"date": "2026-07-01", "value": 332.813, ...},
  "previous": {"date": "2026-06-01", "value": 332.568},
  "deltaAbs": 0.245,
  "deltaPct": 0.0737,
  "attribution": "Source: U.S. Bureau of Labor Statistics via FRED"
}
```

**Cost**: 0 credits. Cached snapshot.

```python
macro_indicator_snapshot("us.cpi.headline")      # CPI
macro_indicator_snapshot("us.rates.fed_funds")    # Fed Funds effective rate
macro_indicator_snapshot(series_id="UNRATE")      # unemployment rate
```

### `macro_indicator_history`

Time series for one indicator.

| Param | Type | Required | Notes |
|---|---|---|---|
| `indicator` OR `series_id` | string | yes | |
| `start_date` / `end_date` | `YYYY-MM-DD` | no | Inclusive bounds |
| `limit` | int | no | 1–500, default 60. Max 500 |
| `take_from` | string | no | `latest` (default) or `earliest` |

**Returns**: array of `{date, value, realtimeStart, realtimeEnd}`. Dates are `YYYY-MM-DD`.

```python
# Full FEDFUNDS history (2009 → today)
macro_indicator_history(series_id="FEDFUNDS", limit=200)
```

**Cost**: 1 credit (data-heavy).

**Pagination**: for series longer than 500 observations (FEDFUNDS goes back to 1954), use `start_date` / `end_date` to slice.

## Catalog (curated ~50)

Selected indicator aliases (full list via `macro_indicator_search()`):

| Alias | FRED ID | Category | Notes |
|---|---|---|---|
| `us.cpi.headline` | `CPIAUCSL` | Inflation | All-items CPI |
| `us.cpi.core` | `CPILFESL` | Inflation | CPI ex food/energy |
| `us.pce.core` | `PCEPILFE` | Inflation | Fed's preferred inflation gauge |
| `us.rates.fed_funds` | `FEDFUNDS` | Rates | Effective fed funds rate |
| `us.yield.10y` | `GS10` | Rates | 10-year Treasury constant maturity |
| `us.yield.2y` | `GS2` | Rates | 2-year Treasury |
| `us.yield_curve.10y_2y` | `T10Y2Y` | Rates | 10y minus 2y — recession signal |
| `us.unemployment_rate` | `UNRATE` | Labor | U-3 |
| `us.nonfarm_payrolls` | `PAYEMS` | Labor | |
| `us.gdp.real` | `GDPC1` | Growth | Real GDP |
| `us.housing_starts` | `HOUST` | Housing | |
| `us.money_supply.m2` | `M2SL` | Liquidity | M2 money stock |
| `us.financial_conditions.nfci` | `NFCI` | Conditions | Chicago Fed NFCI |
| `us.oil.wti_spot` | `DCOILWTICO` | Energy | WTI crude |

For full list: call `macro_indicator_search()` (no params) and inspect the `meta` catalog.

## Common patterns

### Regime overlay on equity returns

```python
# Pull 10y-2y spread for the backtest period
spread = macro_indicator_history("us.yield_curve.10y_2y",
                                  start_date="2020-01-01",
                                  end_date="2026-08-29",
                                  limit=500)
# Negative spread = yield-curve inversion = recession warning
```

### Inflation backdrop for sector allocation

```python
cpi_yoy = ...  # compute YoY% from us.cpi.headline history
# If cpi_yoy > 4% → favor energy / commodities / value
# If cpi_yoy < 2% → favor growth / long duration
```

### Fed cut probability sanity check

`llmquant-macro` gives you the **actual rate path**; `llmquant-polymarket` gives you the **market-implied probability** of cuts. Cross-reference:

```python
fed_path = macro_indicator_history("us.rates.fed_funds", limit=24)
polymarket_event_search("Fed rate cut 2026")  # → 88% "no cuts"
```

## Coverage flags

`meta.coverage_status` is typically `full` for the curated series. Custom / off-catalog series will return `coverage_status: unsupported`. Always cite `attribution` (BLS / BEA / Fed Board etc.) per the backtest-discipline quality rules.

## Frequency mismatch

The series has different cadences:

| Frequency | Examples | Implication |
|---|---|---|
| Daily | Fed Funds, 10y-2y, NFCI, WTI | Can align with daily equity bars |
| Monthly | CPI, PCE, unemployment, housing starts, M2 | Lag equity by 1-2 months |
| Quarterly | GDP, capacity utilization | Far slower |

Don't daily-resample monthly data — it creates spurious precision.

## Workflow Routers

This skill also hosts three macro-analysis workflows (merged from `LLMQuant/skills`). They are prompt-level recipes that orchestrate the MCP tools above into a repeatable deliverable:

| User intent | Workflow |
|---|---|
| Build a full global macro dashboard (growth, inflation, liquidity, rates, FX). | [`workflows/global-macro-dashboard.md`](workflows/global-macro-dashboard.md) |
| Pre-FOMC policy preview with base/bull/bear scenarios. | [`workflows/fed-policy-preview.md`](workflows/fed-policy-preview.md) |
| Translate a macro regime into concrete portfolio tilts. | [`workflows/macro-to-portfolio-impact.md`](workflows/macro-to-portfolio-impact.md) |

Load the matching workflow when the user asks for a macro *deliverable* (dashboard / preview / portfolio impact); use the tool reference above when the user asks for a specific indicator value.

## See also

- `llmquant-polymarket` — for market-implied probabilities (vs actual rates)
- `llmquant-news` — for macro-related company announcements
- `llmquant-data` master — for credit / pagination / error handling