---
name: llmquant-polymarket
description: Polymarket finance-scoped prediction markets via the llmquant-data MCP. Search events, browse by tag/status, read event cards, read individual markets, fetch probability time series (1h/1d). Use for "what's the market-implied probability of X" — Fed cuts, M&A, regulatory outcomes, macroeconomic events.
category: data-source
---

# llmquant-polymarket

Polymarket prediction-market data, **finance-scoped only** (no sports / entertainment / politics noise). Five tools: search, browse, event read, market read, price history.

> Pair with `llmquant-data` master for cross-cutting concerns. This skill is tool-by-tool usage.

## When to use

- "What does the market think about a Fed rate cut in Sept?"
- "Probability of OpenAI getting acquired before 2027"
- "Will the Clarity Act pass this year?"
- Probability time series — track market-implied sentiment over time

## When NOT to use

- **Sports / politics / entertainment** → explicitly out of scope; only finance-tagged events
- **Real-money trading** → this repo is research-only; no live trading
- **Single-binary market making** → Polymarket data only; not an execution venue

## Tools

### `polymarket_event_search`

Semantic search across finance events.

| Param | Type | Required | Notes |
|---|---|---|---|
| `query` | string | yes | Natural language, max 2000 chars |
| `status` | string | no | `active` (default) / `inactive` / `closed` / `active_or_recently_closed` |
| `tag` | string | no | Filter by finance tag, e.g. `crypto`, `fed`, `regulation` |
| `limit` | int | no | 1–20, default 5 |

**Returns**: array of events with full child-market tree (preview). Each event has:

```json
{
  "eventCardId": "b6dbcf60-...",
  "sourceEventId": "51456",
  "sourceEventSlug": "how-many-fed-rate-cuts-in-2026",
  "title": "How many Fed rate cuts in 2026?",
  "description": "...",
  "marketCount": 13,
  "markets": [
    {
      "marketCardId": "0114d70a-...",
      "sourceMarketId": "616902",
      "marketQuestion": "Will no Fed rate cuts happen in 2026?",
      "outcomes": [
        {
          "outcomeId": "...",
          "label": "Yes",
          "outcomeIndex": 0,
          "outcomeTokenId": "12403...",
          "currentProbability": 0.8815,
          "lastPriceTime": "2026-08-29T...",
          "coverageStatus": "cached",
          "coverageReason": null
        },
        {
          "label": "No",
          "currentProbability": 0.1185,
          ...
        }
      ],
      "labels": ["finance", "fed", "federal_reserve", "rate_cut"],
      "status": "active",
      "lifecycleStatus": "open",
      "active": true,
      "closed": false,
      "volume": 7618174.15,
      "liquidity": 465228.86,
      "startTime": "2025-09-29T...",
      "endTime": "2026-12-31T..."
    },
    ...
  ],
  "status": "active",
  "maxMarketVolume": 7618174.15,
  "maxMarketLiquidity": 528782.03
}
```

**Cost**: 1 credit (small queries) to 2 credits (broad searches, when limit > 10).

```python
polymarket_event_search("Fed rate cut 2026", limit=3)
polymarket_event_search("M&A before 2027", tag="crypto", limit=5)
```

### `polymarket_event_browse`

Exact-filter list (no semantic) for paginated discovery.

| Param | Type | Required | Notes |
|---|---|---|---|
| `status` | string | no | `active` (default), `inactive`, `closed`, `active_or_recently_closed` |
| `query` | string | no | Exact lexical filter (NOT semantic) |
| `tag` | string | no | Finance tag, e.g. `crypto` |
| `asset` | string | no | e.g. `BTC`, `ETH`, `SPY` |
| `start_time` / `end_time` | ISO 8601 UTC | no | Must be used together |
| `min_volume` | float | no | Min event-level market volume |
| `min_liquidity` | float | no | Min event-level market liquidity |
| `limit` | int | no | 1–100, default 20 |
| `cursor` | string | no | Pagination cursor from `nextCursor` |

**Returns**: same shape as `event_search`.

```python
# All active crypto-tagged events
polymarket_event_browse(tag="crypto", status="active", limit=20)

# High-volume Fed events
polymarket_event_browse(query="Fed rate", min_volume=1_000_000)
```

**Cost**: 1 credit.

**Note**: Unlike `event_search`, this is **exact lexical filter** — not semantic. Use `event_search` for natural-language discovery.

### `polymarket_event_read`

Read one event card with full child-market previews.

| Param | Type | Required | Notes |
|---|---|---|---|
| `event_card_id` | string (UUID) | yes | From `event_search` / `event_browse` |

**Returns**: same shape as `event_search` results, for one event.

**Cost**: 0 credits.

### `polymarket_market_read`

Read one market card with full outcome detail.

| Param | Type | Required | Notes |
|---|---|---|---|
| `market_card_id` | string (UUID) | yes | From any event |

**Returns**:

```json
{
  "marketCardId": "0114d70a-...",
  "eventCardId": "b6dbcf60-...",
  "eventTitle": "How many Fed rate cuts in 2026?",
  "eventDescription": "...",
  "sourceMarketId": "616902",
  "sourceMarketSlug": "will-no-fed-rate-cuts-happen-in-2026",
  "marketQuestion": "Will no Fed rate cuts happen in 2026?",
  "resolutionCriteria": "...",
  "resolutionSource": null,
  "labels": ["finance", "fed", "federal_reserve", "rate_cut"],
  "financeRelevance": {
    "score": 2,
    "reasons": ["finance_text"],
    "accepted": true,
    "matchedKeywords": ["fed", "federal reserve", "rate cut"]
  },
  "volume": 7618174.15,
  "liquidity": 465228.86,
  "status": "active",
  "lifecycleStatus": "open",
  "outcomes": [
    {
      "outcomeId": "c8fa4634-...",
      "label": "Yes",
      "outcomeIndex": 0,
      "outcomeTokenId": "12403...",
      "currentProbability": 0.8815,
      "lastPriceTime": "2026-08-29T..."
    },
    ...
  ]
}
```

**Cost**: 0 credits.

**Important fields to surface**:
- `marketQuestion`, `currentProbability` per outcome
- `volume` (lifetime USD traded) and `liquidity` (current on-platform depth)
- `endTime` (when the market resolves)
- `resolutionCriteria` (verbatim conditions for resolution)

### `polymarket_price_history`

Probability time series for one outcome.

| Param | Type | Required | Notes |
|---|---|---|---|
| `outcome_token_id` | string | yes | From any market read — identifies the outcome side, not market |
| `interval` | string | yes | `1h` or `1d` |
| `start_time` / `end_time` | ISO 8601 UTC | no | Either or both |
| `limit` | int | no | 1–20000 (1h default 720, 1d default 365) |

**Returns**: array of `{time, probability, price}`. Time at interval boundary.

```python
# Daily probability of "No Fed cuts in 2026" over the last week
polymarket_price_history(
    outcome_token_id="12403...",
    interval="1d",
    limit=5
)
# → 86.5% → 88.0% (Yes probability trending up)
```

**Cost**: 0 credits.

## Patterns

### Fed cut probability tracking

```python
# 1. Find the Fed-cut event
events = polymarket_event_search("Fed rate cut 2026", limit=1)
event = events[0]

# 2. Drill into the "no cuts" market
market = next(m for m in event["markets"] if "no" in m["sourceMarketSlug"])
yes_token = next(o["outcomeTokenId"] for o in market["outcomes"] if o["label"] == "Yes")

# 3. Pull 1-year history
history = polymarket_price_history(
    outcome_token_id=yes_token,
    interval="1d",
    start_time="2025-09-01T00:00:00Z",
    end_time="2026-08-29T00:00:00Z",
    limit=365
)
# Plot: probability of "no cuts" over the year
```

### Cross-reference macro with market pricing

```python
# Compare actual Fed Funds path with market-implied cut probability
fed_path = macro_indicator_history("us.rates.fed_funds", limit=24)
# ... plot alongside polymarket price history
```

### Event scan: all active M&A candidates

```python
events = polymarket_event_search("acquired before 2027", limit=10)
# → Returns event "Which companies will be acquired before 2027?"
# Each market is a single company (Nebius, Perplexity AI, OpenAI, ...)
```

## Edge cases

| Situation | Behavior |
|---|---|
| Empty filter result | Returns `{events: [], count: 0}` cleanly — no error |
| `tag=crypto` with no current crypto events | Empty list, not an error |
| Multi-outcome markets (e.g. "How many cuts?") | One market per strike; pull each separately for full picture |
| Resolved markets | `status: inactive`, `currentProbability` reflects resolution (1.0 or 0.0) |

## Coverage flags

- `coverageStatus: cached` is normal — server caches snapshots
- `coverageReason: null` means data is fresh
- For `closed` markets, probability may not move; check `lastPriceTime`

## Output size

| Call | Approx size |
|---|---:|
| `polymarket_event_search(limit=5)` | ~20-50 KB (full child-market trees) |
| `polymarket_event_browse(limit=20)` | ~50-200 KB |
| `polymarket_market_read` | ~3-10 KB |
| `polymarket_price_history(limit=365)` | ~10-20 KB |

The browse tool can hit truncation thresholds at `limit=100`. Use `event_search` for targeted retrieval.

## See also

- `llmquant-macro` — for the actual macro data (CPI, Fed Funds) to cross-reference
- `llmquant-news` — for related news catalysts
- `llmquant-data` master — for credit / pagination