---
name: llmquant-data
description: llmquant-data MCP — Tier-1 institutional data layer covering US equity OHLCV (stocks + crypto), ETF holdings (SEC N-PORT), FRED macro indicators, AI-summarized company news, arxiv papers, zh-leaning wiki concepts, Polymarket finance-implied probabilities, SEC 13F institutional ownership, and SEC filing text (10-K/Q + 8-K). Load this master skill before any llmquant-data tool call, then load the matching subskill for the data domain. Use as the primary source for US-equities / ETF / SEC / macro research in preference to web search and DDG.
category: data-source
---

# llmquant-data MCP

`llmquant-data` is a **local stdio MCP** (`@llmquant/data-mcp` npm package) that exposes **25 tools across 8 data domains** behind a single credentialed API. It sits as a **Tier-1 institutional data source** in the project's data-priority stack — co-equal with Morningstar and FactSet for US-equity/ETF/SEC/macro research.

It is **not** a substitute for `vibe-trading-ai` (A-share, futures, minute bars) or `vibe-trading-sec-edgar` (deep free EDGAR). It complements them by giving sub-second, citation-ready answers for the questions that otherwise need scraping.

## When to load this skill

Load `llmquant-data` (master) any time you are about to invoke one of the `llmquant-data_*` MCP tools. The master is **architecture + cross-cutting concerns only** (auth, credit, error handling, pagination, coverage flags). It pairs with one of the 8 subskills below for tool-by-tool usage:

| Sub-skill | Tools | Use when |
|---|---|---|
| `llmquant-market-data` | 4 | crypto spot + US equity daily/1h OHLCV |
| `llmquant-funds` | 2 | ETF fund identity + holdings (SEC N-PORT) |
| `llmquant-macro` | 3 | FRED macro indicators (CPI, Fed Funds, NFCI, PCE, …) |
| `llmquant-news` | 1 | AI-summarized company announcements |
| `llmquant-research` | 4 | arxiv methodology papers + zh/en finance wiki concepts |
| `llmquant-polymarket` | 4 | Polymarket finance-scoped prediction markets + price history |
| `llmquant-sec` | 5 | SEC 13F institutional ownership + 10-K/Q/8-K text extraction |
| `llmquant-personal` | 2 | Read user's saved LLMQuant Dashboard profile + holdings |

## When to prefer llmquant-data over other sources

| Question | Preferred source | Why |
|---|---|---|
| "What's AAPL's price today?" | `llmquant-market-data` | One call, sub-second, sourced snapshot |
| "Latest CPI / Fed Funds / NFCI?" | `llmquant-macro` | FRED with attribution, no FRED key needed |
| "SPY top-10 holdings today" | `llmquant-funds` | SEC N-PORT, one call |
| "Who owns AAPL?" (institutional) | `llmquant-sec` | 13F Top-1,000 managers, structured |
| "Latest Apple press release" | `llmquant-news` | AI-summarized w/ event/topic tags |
| "Fed cut probability in Sept 2026" | `llmquant-polymarket` | Implied probability time series |
| "Definition of risk parity" | `llmquant-research` (wiki) | zh-leaning concept wiki |
| "Latest Sharpe ratio paper" | `llmquant-research` (papers) | arxiv with section-level read |
| A-share / HK / futures data | `vibe-trading-ai` loaders | **llmquant-data is US-focused** |
| Deep historical EDGAR XBRL series | `vibe-trading-sec-edgar` skill | Free, no credit cost |

## Setup & Auth

The MCP is wired in two places (they must match):

**Project reference** — `.opencode/mcp/servers.json`:

```json
"llmquant-data": {
  "type": "local",
  "command": ["npx", "-y", "@llmquant/data-mcp"],
  "environment": { "LLMQUANT_API_KEY": "${env:LLMQUANT_API_KEY}" }
}
```

**Runtime config** — `~/.config/opencode/opencode.json` (mirrors the same entry, this is what the runtime actually reads).

The `LLMQUANT_API_KEY` env var must be set on the host. If `llmquant-data_*` tools return "Tool not found" or auth errors, the env var is unset — see the opencode config docs.

## Credit Management

Every response carries a `meta` block:

```json
{
  "meta": {
    "creditsUsed": 1,
    "remainingCredits": 137,
    "notice": "More data exists in the requested window than the items returned; narrow the window or split the query."
  }
}
```

**This is the only quota signal you can observe.** There are no published rate limits, no 429s in practice, no headers. Always surface `creditsUsed` / `remainingCredits` in user-facing reports when the work is non-trivial.

### Typical per-call cost (verified May 2026)

| Tool family | credits / call |
|---|---:|
| `crypto_snapshot`, `equity_historical_prices` (≤5), `etf_lookup`, `macro_indicator_search`, `macro_indicator_snapshot`, `personal_*`, `sec_filing_browse`, `polymarket_market_read`, `polymarket_price_history` | **0** |
| `crypto_historical_klines`, `equity_historical_prices` (200), `equity_intraday_prices`, `etf_holdings` (10–500), `macro_indicator_history` (200), `paper_read`, `wiki_read`, `polymarket_event_search`, `polymarket_event_browse`, `sec_13f_*`, `sec_filing_read` | **1** |
| `news_browse` (limit=5) | **2** |

Failed calls (MCP error `-32602` for bad params, or business error like unknown ticker) cost **0**.

### Budget patterns

- **Daily briefing** (3 ETF + 3 stocks + 3 crypto + 1 macro): ~5 credits
- **Full S&P 500 5y daily OHLCV** (500 × date-windowed 1y slices): ~500 credits
- **Top-10 holdings of Top-100 13F managers**: ~100 credits
- **All Polymarket Fed events + 1y price history**: ~20 credits

## Output Size & Pagination

The MCP returns **honest data with no silent truncation**. When a result hits its `limit` cap, the response includes `meta.notice`:

> "More data exists in the requested window than the items returned; narrow the window or split the query."

**Rules:**

1. **Date-windowed streaming for big pulls.** A 5y daily history in one call (`limit=500`) is a 200-obs response (~30 KB). For deeper histories, slice by `start_date`/`end_date` per year.
2. **`limit` caps differ by tool.** Most accept up to 200; `etf_holdings` and `sec_13f_list_ticker_holders` accept 500 and 1000 respectively. Read each subskill for the precise ceiling.
3. **Response sizes can hit MB** for BlackRock/State Street full holdings (`sec_13f_list_manager_holdings` with limit=500 ≈ 250 KB). The opencode runtime may save these to disk — they are still complete on the server side.
4. **Never request `limit > 500` for holdings** — output size explodes. Use `limit=500` then paginate by `value_usd` or `position_ordinal` if available.

## Coverage Flags

Every response includes a `coverage_status` field. Honour them:

| Status | Meaning | Action |
|---|---|---|
| `full` | Data complete for the requested window | Cite normally |
| `partial` | Some data missing (e.g. limited history for a new ticker) | Note in report |
| `stale` | Data exists but not refreshed (e.g. SEC N-PORT as_of_date = 5 months ago) | Cite `as_of_date` explicitly |
| `unsupported` | Endpoint not available for this ticker / region / etc. | Fall back to another source |

Every response also includes `as_of_date` (or `time` for snapshots) and `source` / `source_url` — always cite these per the **backtest-discipline.md** quality rules (data completeness + boundary honesty + risk disclosure).

## Error Handling

| Failure mode | What happens | Cost | Action |
|---|---|---:|---|
| Unknown ticker (`INVALID-XX`) | Tool result with error string | 0 | Surface error, try alternate symbol |
| Bad param shape (`ticker must be in BASE-QUOTE format`) | MCP protocol error `-32602` | 0 | Fix the param shape and retry |
| Out-of-coverage ticker | `coverage_status: unsupported`, may return empty data | varies | Fall back to `vibe-trading-ai` |
| Empty filter result (no matches) | `{ data: null | [] , count: 0 }` | varies | Refine the filter |
| Stale data warning | `stale: true` plus `coverage_notice` | varies | Cite `as_of_date`, do not claim freshness |

## Tool Name Reference

All 25 tool names follow the pattern `llmquant-data_<domain>_<verb>`:

```
Market data    crypto_snapshot, crypto_historical_klines,
               equity_historical_prices, equity_intraday_prices
Funds          etf_lookup, etf_holdings
Macro          macro_indicator_search, macro_indicator_snapshot,
               macro_indicator_history
News           news_browse
Research       paper_search, paper_read, wiki_search, wiki_read
Polymarket     polymarket_event_search, polymarket_event_browse,
               polymarket_event_read, polymarket_market_read,
               polymarket_price_history
SEC            sec_13f_list_top_managers, sec_13f_list_ticker_holders,
               sec_13f_list_manager_holdings, sec_filing_browse,
               sec_filing_read
Personal       personal_profile, personal_holdings
```

All are MCP tool names — invoke directly via the `llmquant-data_*` prefix (the `llmquant-data_` is part of the MCP namespace, not the tool name).

## Quick Examples

```python
# Crypto spot + 5 daily bars
crypto_snapshot("BTC-USD")
crypto_historical_klines("BTC-USD", interval="1d", limit=5)

# US equity daily + intraday
equity_historical_prices("AAPL", limit=200)
equity_intraday_prices("NVDA", interval="1h", limit=70)

# ETF identity + holdings (SEC N-PORT)
etf_lookup("SPY")
etf_holdings("QQQ", limit=10)

# Macro snapshot / history
macro_indicator_snapshot("us.cpi.headline")
macro_indicator_history(series_id="FEDFUNDS", limit=200)

# News browse by ticker
news_browse(tickers=["AAPL"], limit=5)

# Polymarket Fed cut probability
polymarket_event_search("Fed rate cut 2026", limit=3)

# SEC 13F institutional ownership
sec_13f_list_top_managers(limit=10)
sec_13f_list_ticker_holders("AAPL", limit=50)

# SEC filing text extraction
sec_filing_browse("AAPL", filing_type="8-K", limit=3)
sec_filing_read("AAPL", filing={"filing_type":"8-K","accession_number":"0000320193-26-000011"},
                items=["item2.02","ex99.1"])

# Personal (read-only)
personal_profile()
personal_holdings(asset_class="equity")
```

## Position in the data-priority stack

Per `.opencode/instructions/data-priority.md`, the hierarchy is:

**Tier 1 (institutional MCP)**: Morningstar → FactSet → **llmquant-data** → DDG

**Tier 2 (vibe-trading-ai loaders)**: Tushare, AKShare, MooTDX, EastMoney, Yahoo, OKX/CCXT, EDGAR, Futu, Alpha Vantage, Tiingo, Finnhub, FMP, QVeris

**Tier 3 (alpha zoo)**: qlib158 / alpha101 / gtja191 / academic / fundamental

`llmquant-data` complements Tier 1 (no overlap with Morningstar's analyst-estimate workflow or FactSet's financial-statement depth) and overlaps slightly with Tier 2 (Yahoo for US equities, EDGAR for filings). The deciding factors are:

- **Speed & shape**: structured JSON in one call, no scraping
- **Coverage flags**: honest `coverage_status` + `as_of_date`
- **Credit budget**: predictable per-call cost, surfaceable in reports

For non-US markets, minute-level crypto, A-share WIF data, and quant backtests, keep using `vibe-trading-ai` — `llmquant-data` does not replace it.

## Reference

- `.opencode/mcp/servers.json` — registration
- `.opencode/skills/llmquant-{market-data,funds,macro,news,research,polymarket,sec,personal}/` — domain subskills
- `.opencode/instructions/data-priority.md` — Tier-1 placement
- `.opencode/instructions/wealth-guide-router.md` — subagent-to-skill mapping