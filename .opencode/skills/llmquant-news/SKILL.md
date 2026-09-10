---
name: llmquant-news
description: AI-summarized company announcements (earnings, M&A, guidance, leadership, etc.) via the llmquant-data MCP. Browse by ticker, event type, or topic. Use for post-earnings summaries, product-launch briefs, or any "what happened at company X recently" question.
category: data-source
---

# llmquant-news

Single browse-style tool that returns **AI-summarized company announcements** with structured metadata (event type, topic tags, source URL, publication date).

> Pair with `llmquant-data` master for cross-cutting concerns. This skill is tool-by-tool usage.

## When to use

- "Latest news on AAPL" / "what did Apple announce this quarter"
- Pull all earnings releases (event=`earnings`) for a coverage universe
- Find all M&A / leadership_change events in a sector
- Pull recent product launches for tech names

## When NOT to use

- **Sentiment / social media** → not in scope (use `vibe-trading-ai` sentiment tools)
- **Real-time breaking news** → this is a curated, AI-summarized feed, not a firehose
- **Deep transcript / 10-Q MD&A reading** → `llmquant-sec`
- **Macro news** (Fed minutes, CPI release) → `llmquant-macro` or web search

## Tool

### `news_browse`

Browse recent company announcements.

| Param | Type | Required | Notes |
|---|---|---|---|
| `tickers` | string[] | no | Up to 5 tickers, OR'd together. e.g. `["AAPL", "MSFT"]` |
| `events` | enum[] | no | Controlled values, OR'd. See table below |
| `topics` | enum[] | no | Controlled values, OR'd. See table below |
| `start_date` / `end_date` | `YYYY-MM-DD` | no | Inclusive UTC window. Must be used together |
| `limit` | int | no | 1–25, default 10 |

**Returns**:

```json
{
  "items": [
    {
      "title": "Apple introduces new Mac Studio with M5 Max and M5 Ultra",
      "abstract": "Apple announced the new Mac Studio with M5 Max and the all-new M5 Ultra, ...",
      "summary": "Apple announced the new Mac Studio, powered by M5 Max and the all-new M5 Ultra, with up to 4.3x faster AI performance, up to 1.8x faster graphics, ..., with availability beginning September 22; the 512GB configuration is expected in late October.",
      "events": ["product"],
      "topics": ["artificial_intelligence", "consumer_electronics"],
      "tickers": ["AAPL"],
      "published_at": "2026-08-25",
      "source_url": "https://www.apple.com/newsroom/2026/08/apple-introduces-new-mac-studio-with-m5-max-and-m5-ultra/"
    },
    ...
  ],
  "count": 5
}
```

**Fields to surface in reports**: `title`, `abstract`, `published_at`, `source_url`, `events`, `topics`. The `summary` is the AI-generated digest (multi-paragraph); `abstract` is one-sentence.

**Cost**: 2 credits per call (most expensive single tool — AI summarization is metered).

```python
news_browse(tickers=["AAPL"], limit=5)
# → 5 most recent AAPL announcements

news_browse(events=["earnings"], start_date="2026-08-01", end_date="2026-08-29", limit=20)
# → all earnings releases in the window

news_browse(topics=["artificial_intelligence"], events=["product"], limit=20)
# → AI-related product launches across all tickers
```

## Controlled enums

### Events (20 values)

```
earnings, guidance, m_and_a, partnership, product, regulatory_approval,
regulatory, legal, leadership_change, workforce, restructuring,
bankruptcy, capital_action, credit_rating, analyst_rating,
accounting_audit, operational_incident, shareholder_meeting,
strategic_update, other
```

### Topics (43 values — financial-sector taxonomy)

```
semiconductors, software, cloud_computing, cybersecurity, artificial_intelligence,
consumer_electronics, it_hardware_networking, telecommunications, media_entertainment,
internet_services, biotech_pharma, medical_devices, life_sciences_tools,
healthcare_services, banking, capital_markets, insurance, fintech,
crypto_digital_assets, real_estate, automotive, retail, consumer_packaged_goods,
apparel_luxury, restaurants_leisure, aerospace_defense, industrial_machinery,
transportation_logistics, construction_engineering, business_services,
oil_gas, renewable_energy, utilities, metals_mining, chemicals,
agriculture_food_production, paper packaging_forestry, environmental_services,
space_economy, quantum_computing, data_centers,
macroeconomics_policy, geopolitics_trade
```

Unknown enum values should be ignored (passed-through, but the server returns zero matches if any value is invalid).

## Coverage flags

- `coverage_status` is **not surfaced** in `news_browse` responses (no `meta.coverage_status` here)
- Coverage is by ticker + date — well-covered names (mega-cap US) return 5+ items per week; small caps return fewer
- Filter by `start_date`/`end_date` to scope a window

## Patterns

### Earnings-release sweep

```python
earnings = news_browse(
    events=["earnings"],
    start_date="2026-07-01", end_date="2026-08-29",
    limit=25
)
# Pull all earnings press releases in the last 2 months
```

### Sector M&A scan

```python
mna = news_browse(
    events=["m_and_a"],
    topics=["banking", "insurance", "fintech"],
    start_date="2026-01-01", end_date="2026-08-29",
    limit=25
)
```

### Single-name briefing

```python
# 5 most recent AAPL items
items = news_browse(tickers=["AAPL"], limit=5)["items"]
# Pair with llmquant-sec for 8-K text extraction on the most relevant filing
```

## Edge cases

| Situation | Behavior |
|---|---|
| Ticker not in coverage | Returns empty `items[]`; no error |
| Invalid enum value | Empty result (no error) |
| Date window too wide | Returns most recent first (`take_from=latest` default), capped at `limit` |
| Multiple tickers | OR'd: items tagged with ANY of the tickers |
| Same event in multiple sources | Returns each separately (e.g. apple.com newsroom + nasdaq press release) |

## Output size

`news_browse(limit=25)` ≈ 30–80 KB depending on summary length. Safe in batch.

## See also

- `llmquant-sec` — for the underlying 8-K text when the news item is a regulatory filing
- `llmquant-market-data` — for price action around announcement dates
- `llmquant-polymarket` — for market-implied reactions to macro/policy news