---
name: llmquant-funds
description: ETF fund identity + holdings via the llmquant-data MCP. Fund lookup (issuer, AUM, expense, top-10) and full holdings (SEC N-PORT, latest quarterly snapshot). Use for SPY/QQQ/VTI/IBIT/SOXX/ARKK overlap analysis, AUM tracking, or any "what's in this ETF" question.
category: data-source
---

# llmquant-funds

ETF fund identity and full holdings via **SEC N-PORT** (the regulatory snapshot funds file quarterly). Two tools, read-only.

> Pair with `llmquant-data` master for cross-cutting concerns (credit, error handling). This skill is tool-by-tool usage.

## When to use

- "What's in SPY?" / "Top 10 holdings of QQQ?"
- ETF overlap analysis (do SPY and VTI overlap > 90%?)
- Fund identity / AUM / expense ratio snapshot
- Concentration / sector / asset-type breakdown

## When NOT to use

- **ETF prices / intraday bars** → `llmquant-market-data`
- **Mutual funds (open-end)** → not yet supported by `llmquant-data`; use `morningstar` MCP or `vibe-trading-quanta`
- **Daily constituent changes** → N-PORT is **quarterly**; for daily holdings use issuer site or `qveris`

## Tools

### `etf_lookup`

Fund identity card for one ETF.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | e.g. `SPY`, `QQQ`, `VTI`. Case-insensitive |
| `as_of` | `YYYY-MM-DD` | no | Returns latest snapshot at or before this date |

**Returns**:

```json
{
  "ticker": "SPY",
  "fund_name": "SPDR S&P 500 ETF Trust",
  "issuer": "spdr",
  "asset_class": "equity",
  "category": "Broad U.S. Equity",
  "cik": "0000884394",
  "series_id": null,
  "class_id": null,
  "expense_ratio": null,
  "aum": 651588269947.59,        // dollars
  "nav": null,
  "market_price": null,
  "premium_discount_pct": null,
  "inception_date": null,
  "holdings_count": 503,          // total
  "top_holdings": [               // up to 10
    {
      "holding_name": "NVIDIA Corp",
      "ticker": null,
      "isin": "US67066G1040",
      "cusip": "67066G104",
      "sector": null,
      "country": "US",
      "asset_type": "equity",
      "weight": 0.07577613507003, // decimal (7.58%)
      "market_value": 49374840753.6
    },
    ...
  ],
  "sector_exposure": null,        // not yet populated
  "country_exposure": null,
  "asset_type_exposure": null,
  "source": "sec_nport",
  "as_of_date": "2026-03-31",
  "stale": false,
  "coverage_status": "full"
}
```

**Key fields to surface in reports**: `fund_name`, `issuer`, `aum`, `holdings_count`, `top_holdings[]`, `as_of_date`, `coverage_status`.

**Cost**: 0 credits. Free lookup.

```python
etf_lookup("SPY")
etf_lookup("QQQ")
etf_lookup("IBIT")  # returns coverage_status="unsupported" — BlackRock IBIT not in current snapshot
```

### `etf_holdings`

Full holdings table with shares, market_value, ISIN/CUSIP, weight.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | ETF ticker |
| `limit` | int | no | 1–500 (default 50). Max 500 |
| `as_of` | `YYYY-MM-DD` | no | Latest snapshot ≤ as_of |

**Returns**:

```json
{
  "ticker": "QQQ",
  "fund_name": "Invesco QQQ Trust, Series 1",
  "issuer": "invesco",
  "holdings": [
    {
      "isin": "US67066G1040",
      "cusip": "67066G104",
      "sedol": null,
      "sector": null,
      "shares": 185426246,
      "ticker": null,
      "weight": 0.08681262560507,
      "country": "US",
      "asset_type": "equity",
      "holding_name": "NVIDIA Corp.",
      "market_value": 32338337302.4,
      "notional_value": null,
      "position_ordinal": 1,
      "source": "sec_nport",
      "as_of_date": "2026-03-31"
    },
    ...
  ],
  "source": "sec_nport",
  "as_of_date": "2026-03-31",
  "fetched_at": "2026-08-11T13:30:03.942728+00:00",
  "stale": false,
  "coverage_status": "full",
  "coverage_notice": "Holdings reflect the latest available SEC N-PORT regulatory snapshot (31-MAR-2026) for QQQ; this is not current daily issuer holdings."
}
```

**Important nuances**:

1. **`ticker` field is nullable** for bonds, cash, derivatives, and non-U.S. positions. **Always use `cusip` or `isin` for cross-fund overlap computation** — never trust the ticker for matching.
2. **`sector` is null** in N-PORT — fund-level sector breakdowns (`sector_exposure`) are not populated. Compute your own sector classification client-side.
3. **`market_value` is in dollars**; `weight` is decimal (0.075 = 7.5%). They should agree (weight × AUM ≈ market_value) but don't always exactly — use `market_value` for precise work.
4. **Coverage**: at the time of writing, **BlackRock IBIT and DRAM return `unsupported`** (no N-PORT coverage). Document the coverage_status before claiming "IBIT has X% BTC exposure".

**Cost**: 0 credits for `limit ≤ 10`, 1 credit for full holdings.

```python
# Top 10 holdings of QQQ (free)
etf_holdings("QQQ", limit=10)

# All 503 SPY holdings — careful, ~250 KB response
etf_holdings("SPY", limit=500)
```

## Output sizes

| Call | Approx size |
|---|---:|
| `etf_lookup` | < 5 KB |
| `etf_holdings(limit=10)` | < 20 KB |
| `etf_holdings(limit=500)` (SPY/QQQ) | ~250 KB |

The 500-row response is borderline for the opencode runtime's display truncation (~256 KB). For SPY specifically (503 holdings total) you cannot get the bottom 3 via a single call; use `limit=500` then `cursor` (when added) or `position_ordinal > 500` if the API extends.

## Coverage caveats

| Caveat | Implication |
|---|---|
| N-PORT is **quarterly** with ~3-5 month lag | Don't claim "current" holdings; always cite `as_of_date` |
| `coverage_status: unsupported` for IBIT / DRAM | Use alternative sources for Bitcoin/Ethereum spot ETFs from BlackRock |
| Holdings drift daily but the snapshot doesn't | For "today's overlap", acknowledge the date stamp |
| Country code may be `IE` (Ireland) for ADRs / dual-listings | Expected, not a data quality issue |

## Patterns

### Top-10 concentration check

```python
data = etf_lookup("SPY")
top10 = data["top_holdings"]
top10_weight = sum(h["weight"] for h in top10)
# top10_weight ≈ 0.36 (36%) — high concentration
```

### Cross-fund overlap (use cusip, not ticker)

```python
spy = {h["cusip"]: h["weight"] for h in etf_holdings("SPY", limit=500)["holdings"]}
qqq = {h["cusip"]: h["weight"] for h in etf_holdings("QQQ", limit=500)["holdings"]}

overlap = set(spy) & set(qqq)
overlap_weight_spy = sum(spy[c] for c in overlap)  # how much of SPY is also in QQQ
overlap_weight_qqq = sum(qqq[c] for c in overlap)  # how much of QQQ is also in SPY
```

### Sector breakdown (compute client-side)

```python
holdings = etf_holdings("VTI", limit=500)["holdings"]
# Pass to a sector classifier (GICS / custom) for sector exposure — llmquant-data does not populate sector_exposure yet
```

## See also

- `llmquant-sec` — for 13F institutional ownership of ETF issuers / top holders
- `llmquant-market-data` — for ETF price bars
- `llmquant-macro` — overlay macro regime on sector allocation