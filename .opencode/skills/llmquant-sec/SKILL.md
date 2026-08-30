---
name: llmquant-sec
description: SEC institutional ownership (13F) + filing text extraction (10-K / 10-Q / 8-K) via the llmquant-data MCP. Top-1,000 manager rosters, per-ticker holders lists, single-manager holdings detail, filing browse + section-level read (MD&A, ex99.1 earnings press release, risk factors). Use for "who owns X", "what did Berkshire buy/sell", "extract the latest Apple 8-K earnings release", or any institutional-ownership / SEC-text-mining task.
category: data-source
---

# llmquant-sec

Two related families:

1. **SEC 13F** — institutional ownership (quarterly Form 13F-HR filings of Top-1,000 managers)
2. **SEC filings** — text extraction from 10-K / 10-Q / 8-K with section-level reads

Five tools, all read-only.

> Pair with `llmquant-data` master for cross-cutting concerns. This skill is tool-by-tool usage.

## When to use

- "Who owns AAPL?" → 13F ticker holders list
- "What are Berkshire's top holdings?" → 13F manager holdings
- "Top-10 institutional managers by AUM" → 13F top managers
- "Latest Apple 10-Q MD&A section" → SEC filing read
- "Apple's Q2 earnings press release" → SEC 8-K ex99.1 read

## When NOT to use

- **Free deep historical EDGAR XBRL series** → `sec-edgar` (free, no credits, but slower)
- **Insider trades (Form 4)** → not in `llmquant-data`; use `sec-edgar` or `edgar-sec-filings`
- **Proxy / DEF 14A / Section 16 specifics** → may be covered; check `sec_filing_browse` first
- **Private fund / non-13F institutional ownership** → out of scope (only registered investment advisers with $100M+ AUM file 13F)

---

## SEC 13F (institutional ownership)

### Coverage semantics (read first)

- **Top-1,000 manager set** only — not full-market ownership
- **5 quarters available** at the time of writing: 2025-03-31 through 2026-03-31
- **Reportable value** is an **AUM proxy** — excludes fixed income, options, non-U.S. holdings, and shorts
- **Each quarter has its own Top-1,000** — rosters change across quarters as managers move in and out
- **An older quarter's roster stays stable** when a newer quarter is released

### `sec_13f_list_top_managers`

List the Top-N managers for a quarter.

| Param | Type | Required | Notes |
|---|---|---|---|
| `limit` | int | no | 1–1000, default 30 |
| `year` + `quarter` | int + int | no | Both required together. Defaults to latest covered quarter |

**Returns**:

```json
{
  "manager_set_period": "2026-03-31",
  "ranking_period": "2026-03-31",
  "managers": [
    {
      "manager_cik": "2012383",
      "manager_name": "BlackRock, Inc.",
      "aliases": ["BLACKROCK"],
      "period_rank": 1,
      "period_reportable_value_usd": 5723531457401
    },
    {
      "manager_cik": "93751",
      "manager_name": "STATE STREET CORP",
      ...
      "period_rank": 2,
      "period_reportable_value_usd": 2896359015041
    },
    ...
  ]
}
```

**Cost**: 0 credits. Cached ranking.

```python
sec_13f_list_top_managers(limit=10)
sec_13f_list_top_managers(limit=1000, year=2025, quarter=4)
```

### `sec_13f_list_ticker_holders`

List institutional managers that hold a given ticker.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | e.g. `NVDA`, `AAPL`. Case-insensitive; `BRK.B` → `BRK-B` |
| `year` + `quarter` | int + int | no | Defaults to latest covered quarter |
| `limit` | int | no | 1–1000, default 100 |

**Returns**:

```json
{
  "ticker": "NVDA",
  "ranking_period": "2026-03-31",
  "total_holders_in_scope": 773,
  "aggregate_value_usd": 2375740502332,
  "holders": [
    {
      "manager_cik": "2012383",
      "manager_name": "BlackRock, Inc.",
      "manager_period_reportable_value_usd": 5723531457401,
      "manager_period_of_report": "2026-03-31",
      "manager_period_rank": 1,
      "accession_number": "0002012383-26-001841",
      "cusip": "67066G104",
      "title_of_class": "COM",
      "value_usd": 336352928002,
      "shares": 1928629174,
      "shares_type": "SH"
    },
    ...
  ]
}
```

**Important fields**:
- `value_usd` — current dollar value of the holding as of the report period
- `shares` — number of shares held (NOT % of outstanding)
- `shares_type` — `SH` (sole), `SH-PRN` (shared), etc.
- `cusip` — canonical identifier (CUSIP is the right key for any cross-manager overlap computation)

**Cost**: 1 credit (small lists) — capped server-side at 1000.

```python
sec_13f_list_ticker_holders("AAPL", limit=50)
```

### `sec_13f_list_manager_holdings`

All holdings reported by one manager.

| Param | Type | Required | Notes |
|---|---|---|---|
| `manager_cik` OR `manager_name` | string | yes | One required; CIK preferred |
| `year` + `quarter` | int + int | no | Defaults to latest covered quarter |
| `limit` | int | no | 1–500, default 200 |

**Returns**:

```json
{
  "ranking_period": "2026-03-31",
  "manager": {
    "manager_cik": "2012383",
    "manager_name": "BlackRock, Inc.",
    "latest_reportable_value_usd": 5723531457401,
    "period_rank": 1,
    "period_reportable_value_usd": 5723531457401,
    "is_in_covered_manager_set": true
  },
  "filing": {
    "filing_type": "13F-HR",
    "accession_number": "0002012383-26-001841",
    "filed_at": "2026-05-13",
    "period_of_report": "2026-03-31",
    "is_amendment": false,
    "table_entry_total": 50651,
    "table_value_total": 5723531457401
  },
  "holdings": [
    {
      "cusip": "67066G104",
      "ticker": "NVDA",
      "name_of_issuer": "NVIDIA CORPORATION",
      "title_of_class": "COM",
      "value_usd": 125565428123,
      "shares": 719985253,
      "shares_type": "SH",
      "investment_discretion": "SOLE",
      "voting_sole": 719985253,
      "voting_shared": 0,
      "voting_none": 0,
      "put_call": null
    },
    ...
  ]
}
```

**Important**: For huge managers (BlackRock, State Street), `limit=500` returns top-500 by `value_usd`. Total holdings in the filing may be 30K-50K+. To see beyond top-500, paginate by `value_usd` (not directly supported — use multiple quarters or accept the top-N view).

**Voting fields**: `voting_sole` + `voting_shared` + `voting_none` should sum to `shares`. Useful for activism / governance analysis.

**Cost**: 1 credit. BlackRock full holdings at `limit=500` ≈ 250 KB response.

```python
# BlackRock (CIK 2012383)
sec_13f_list_manager_holdings(manager_cik="2012383", limit=20)

# Berkshire (CIK 1067983) — resolves automatically
sec_13f_list_manager_holdings(manager_cik="1067983", limit=30)
```

### Manager-name resolution

`sec_13f_list_manager_holdings` accepts `manager_name` and resolves server-side:

- **0 candidates** → 200 with empty data + explanatory notice
- **Multiple candidates** → `invalid_request` asking for `manager_cik`
- **Single match** → auto-resolved

Always pass `manager_cik` if you have it (faster, deterministic).

## 13F patterns

### Concentration / ownership pie

```python
holders = sec_13f_list_ticker_holders("NVDA", limit=100)
top10_value = sum(h["value_usd"] for h in holders["holders"][:10])
total = holders["aggregate_value_usd"]
top10_share = top10_value / total  # ~0.45 typical for mega-cap
```

### Quarter-over-quarter drift

```python
for year, quarter in [(2025, 4), (2026, 1)]:
    h = sec_13f_list_ticker_holders("AAPL", year=year, quarter=quarter, limit=100)
    # diff against prior to find new positions / exits
```

### Smart-money signal (Berkshire's new positions)

```python
# Q1 2026
current = {h["cusip"]: h for h in sec_13f_list_manager_holdings(manager_cik="1067983", limit=200)["holdings"]}
# Q4 2025 (compare)
prior   = {h["cusip"]: h for h in sec_13f_list_manager_holdings(manager_cik="1067983", limit=200, year=2025, quarter=4)["holdings"]}

new_positions = set(current) - set(prior)
exits = set(prior) - set(current)
```

---

## SEC Filings (10-K / 10-Q / 8-K text)

### `sec_filing_browse`

Recent filings for a ticker.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | e.g. `AAPL` |
| `filing_type` | string | no | `10-K` / `10-Q` / `8-K` (omit = all) |
| `limit` | int | no | 1–50, default 10 |

**Returns**: array of:

```json
{
  "ticker": "AAPL",
  "companyName": "Apple Inc.",
  "filingType": "8-K",
  "accessionNumber": "0000320193-26-000011",
  "filingDate": "2026-04-30",
  "reportDate": "2026-04-30",
  "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019326000011/aapl-20260430.htm",
  "sectionKeys": ["item2.02", "item9.01", "ex99.1"]
}
```

**Two-step pattern** (browse → read): never read a filing without first browsing to get the `accessionNumber`.

```python
recent = sec_filing_browse("AAPL", filing_type="8-K", limit=5)
# Pick the latest earnings 8-K (typically has item2.02 + ex99.1)
for f in recent:
    if "ex99.1" in f["sectionKeys"]:
        target = f
        break
```

**Cost**: 0 credits.

### `sec_filing_read`

Read one or more sections of a filing.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | |
| `filing` | object | yes | Three shapes — see below |
| `items` | string[] | no | Section codes; omit = all available |

**Three `filing` shapes** (mutually exclusive):

| Shape | When to use |
|---|---|
| `{"filing_type":"10-K", "year":2024}` | Read latest 10-K for fiscal year 2024 |
| `{"filing_type":"10-Q", "year":2025, "quarter":2}` | Read Q2 2025 10-Q |
| `{"filing_type":"10-K"\|"10-Q"\|"8-K", "accession_number":"0000320193-26-000011"}` | Read exact filing — **required for 8-K** (8-Ks are event-driven) |

**Returns**:

```json
{
  "ticker": "AAPL",
  "filingType": "8-K",
  "accessionNumber": "0000320193-26-000011",
  "availableSections": [
    {"sectionKey": "item2.02", "sectionTitle": "Results of Operations and Financial Condition", "ordinal": 1, "charCount": 702},
    {"sectionKey": "item9.01", ..., "charCount": 231},
    {"sectionKey": "ex99.1", ..., "charCount": 11986}
  ],
  "items": [
    {
      "number": "item2.02",
      "name": "Item 2.02: Results of Operations and Financial Condition",
      "text": "..."
    },
    {
      "number": "ex99.1",
      "name": "EX-99.1",
      "text": "Apple reports second quarter results ... [full press release with 3-statement tables]"
    }
  ]
}
```

**Section codes** depend on filing type:

| Filing | Common sections |
|---|---|
| 10-K | `1` (Business), `1A` (Risk Factors), `7` (MD&A), `8` (Financial Statements) |
| 10-Q | `part1item1` (Financials), `part1item2` (MD&A), `part2item1a` (Risk Factors update) |
| 8-K | `item2.02` (Earnings press release), `item5.02` (Leadership change), `item9.01` (Exhibits), `ex99.1` (Press release exhibit) |

**Cost**: 1 credit.

**Output size**: An ex99.1 earnings press release (with 3-statement tables) is ~12 KB. A full 10-K MD&A + financial statements can be 100-300 KB — may trigger opencode runtime truncation.

**Important rule for 8-K**: must use `accession_number` shape. `year`/`quarter` will NOT work for 8-K (event-driven).

```python
# Earnings press release extraction (8-K item2.02 + ex99.1)
sec_filing_read(
    ticker="AAPL",
    filing={"filing_type":"8-K", "accession_number":"0000320193-26-000011"},
    items=["item2.02", "ex99.1"]
)

# 10-K MD&A for fiscal 2024
sec_filing_read(
    ticker="MSFT",
    filing={"filing_type":"10-K", "year":2024},
    items=["7"]  # MD&A section
)
```

## Filing patterns

### Quarterly earnings walk

```python
# 1. Browse to find the latest 8-K (earnings release)
recent = sec_filing_browse("NVDA", filing_type="8-K", limit=10)
earnings_8k = next(f for f in recent if "ex99.1" in f["sectionKeys"])

# 2. Read item2.02 + ex99.1 (the actual press release)
filing = sec_filing_read(
    ticker="NVDA",
    filing={"filing_type":"8-K", "accession_number": earnings_8k["accessionNumber"]},
    items=["item2.02", "ex99.1"]
)
# Extract revenue / EPS / segment data from ex99.1 text
```

### Risk-factor extraction (10-K)

```python
sec_filing_read(
    ticker="TSLA",
    filing={"filing_type":"10-K", "year":2024},
    items=["1A"]  # Risk Factors
)
```

### Compare two quarterly MD&As

```python
q1 = sec_filing_read(ticker="GOOG", filing={"filing_type":"10-Q", "year":2025, "quarter":1}, items=["part1item2"])
q2 = sec_filing_read(ticker="GOOG", filing={"filing_type":"10-Q", "year":2025, "quarter":2}, items=["part1item2"])
# Diff to surface management commentary changes
```

## Coverage flags

- 13F tools always return `coverage_status`-equivalent notice strings
- Filing read returns `availableSections` even when the requested `items` are absent (dropped silently)
- If `items` is requested but none exist, `items` returns `[]` with an explanatory notice

## Output size

| Call | Approx size |
|---|---:|
| `sec_filing_browse(limit=10)` | < 10 KB |
| `sec_filing_read(8-K ex99.1)` | ~12 KB |
| `sec_filing_read(10-Q part1item2)` | ~30-50 KB |
| `sec_filing_read(10-K item 7)` | ~80-150 KB |
| `sec_13f_list_top_managers(limit=1000)` | ~50 KB |
| `sec_13f_list_ticker_holders(limit=1000)` | ~300 KB |
| `sec_13f_list_manager_holdings(limit=500)` | ~250 KB |

13F `limit=1000` and full-10-K reads can hit the opencode runtime's display truncation threshold (~256 KB). Use `items=["1A"]` for focused reads.

## See also

- `sec-edgar` skill — for free, no-credit XBRL series and edge cases llmquant-data doesn't cover
- `llmquant-news` — for AI-summarized company announcements (high-signal pre-filter before reading the full 8-K)
- `llmquant-data` master — for credit / pagination / error handling