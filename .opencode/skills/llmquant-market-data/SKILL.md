---
name: llmquant-market-data
description: Crypto spot + US equity OHLCV via the llmquant-data MCP. Crypto snapshots (BTC/ETH/SOL/…), crypto daily/4h/1h/1w klines, US equity daily bars, US equity 1h intraday bars (14-day max window). Use for any US-equity or crypto price question in preference to web search or yfinance.
category: data-source
---

# llmquant-market-data

Real-time and historical OHLCV for **crypto spot** (top BASE-QUOTE pairs) and **US equity** (NYSE / NASDAQ / ^GSPC-style indices). Four tools, all read-only.

> Pair with `llmquant-data` master for cross-cutting concerns (credit, error handling, pagination). This skill is tool-by-tool usage.

## When to use

- Spot / historical price for a US equity or crypto pair
- Intraday (1h) bars for the last 14 calendar days
- Dividend / split-adjusted daily history (up to 200 bars per call)

## When NOT to use

- **A-shares / HK / futures** → `vibe-trading-ai` (mootdx / akshare / tushare)
- **Minute / tick bars** → `vibe-trading-ai`; `llmquant-data` caps at 1h
- **Options / implied vol** → `qveris` marketplace
- **Fundamentals / earnings** → `llmquant-sec` (filings) or `llmquant-news`

## Tools

### `crypto_snapshot`

Latest price + 24h stats for one crypto ticker.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | BASE-QUOTE format (e.g. `BTC-USD`). Regex: `^[A-Za-z]+-[A-Za-z]+$` |

**Returns**: `{price, ticker, dayChange, dayChangePercent, volume24h, time}` — `volume24h` is in **BASE** units.

```python
crypto_snapshot("BTC-USD")        # → $77,542.75, 24h -2.10%, vol 15,995 BTC
crypto_snapshot("ETH-USD")        # → $2,432.87, 24h -1.99%
crypto_snapshot("SOL-USD")        # → $103.17,   24h -1.59%
```

**Cost**: 0 credits. **Frequency**: free to call (no observed throttling).

**Errors**:
- Unknown pair (`INVALID-XX`) → tool result with error string, **no charge**
- Malformed (`badformat`) → MCP error `-32602`, **no charge**

### `crypto_historical_klines`

OHLCV candles for a crypto ticker.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | BASE-QUOTE |
| `interval` | string | yes | `1h` / `4h` / `1d` / `1w` |
| `limit` | int | no | 1–200 (default varies by interval: 1h=24, 4h=42, 1d=30, 1w=12) |
| `start_time` / `end_time` | ISO 8601 UTC | no | e.g. `2026-03-01T00:00:00Z` |
| `take_from` | string | no | `latest` (default) or `earliest` |

**Returns**: array of `{open, high, low, close, volume, time}`. Times are ISO UTC. `volume` is in BASE units.

```python
# Last 5 daily candles for BTC
crypto_historical_klines("BTC-USD", interval="1d", limit=5)
```

**Cost**: 1 credit (data-heavy).  
**Pagination**: when the limit is below the available data, response includes `meta.notice` — narrow the window with `start_time`/`end_time` or split.

### `equity_historical_prices`

US equity **daily** OHLCV. Adjusted for splits and dividends.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | e.g. `AAPL`, `MSFT`, `BRK.B`, `^GSPC` (index) |
| `start_date` / `end_date` | `YYYY-MM-DD` | no | Inclusive bounds |
| `limit` | int | no | 1–200 (default 30). Mutual exclusion with start/end matters — see below |
| `take_from` | string | no | `latest` (default) or `earliest` |

**Returns**: array of `{open, high, low, close, volume, adjustedClose, dividend, stockSplit, time}`. Time is `YYYY-MM-DD`.

- `adjustedClose` accounts for splits + dividends retroactively
- `dividend` is per-bar cash dividend (USD); `stockSplit` is the split ratio for the bar
- Use `adjustedClose` for return calculations; use raw `close` to reconstruct the original price series

```python
# 1-year daily history for AAPL
equity_historical_prices("AAPL", limit=200)

# Exact 2025 calendar year
equity_historical_prices("AAPL", start_date="2025-01-01", end_date="2025-12-31")
```

**Cost**: 0 credits for `limit ≤ 5` (free preview), 1 credit for full data.  
**Pagination**: `limit=200` ≈ 9.5 months of trading days; for multi-year, slice by year with `start_date`/`end_date`.

**Ticker normalization**: BRK.B → BRK-B (server-side), case-insensitive. Index tickers like `^GSPC` are supported.

### `equity_intraday_prices`

US equity **1h** intraday OHLCV. **14-day max window**.

| Param | Type | Required | Notes |
|---|---|---|---|
| `ticker` | string | yes | Same as above |
| `interval` | string | yes | `1h` only (currently) |
| `start_date` / `end_date` | `YYYY-MM-DD` | no | 14-day max window |
| `limit` | int | no | 1–70 (default 35). Max 70 |
| `take_from` | string | no | `latest` (default) or `earliest` |

**Returns**: array of `{open, high, low, close, volume, time}`. Times are ISO UTC at the hour mark (`15:30:00Z` is US market open).

**Cost**: 1 credit.  
**Window limit**: server rejects windows >14 calendar days; if `start_date` is more than 14 days back, returns an error. Use `equity_historical_prices` for longer backtests.

```python
# Last 5 hours of NVDA
equity_intraday_prices("NVDA", interval="1h", limit=5)
```

## Patterns

### Intraday + daily blend

```python
# Latest day daily bar
daily = equity_historical_prices("AAPL", limit=1)

# Last 14 days hourly for short-term volatility calc
intra = equity_intraday_prices("AAPL", interval="1h", start_date="...", end_date="...", limit=70)
```

### Crypto + equity portfolio snapshot

```python
# 8 calls in parallel: 4 crypto + 4 equity
# Total: ~0 credits (all snapshots / 5-day history are free preview)
for t in ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD"]:
    crypto_snapshot(t)
for t in ["AAPL", "MSFT", "NVDA", "SPY"]:
    equity_historical_prices(t, limit=5)
```

### Multi-year backtest

Don't request `limit=5000`. Stream by year:

```python
for year in range(2020, 2027):
    bars = equity_historical_prices("AAPL",
                                     start_date=f"{year}-01-01",
                                     end_date=f"{year}-12-31",
                                     limit=260)
    # append to local frame
```

## Output size

| Call | Approx response size |
|---|---:|
| `crypto_snapshot` | < 1 KB |
| `crypto_historical_klines(limit=200)` | ~15 KB |
| `equity_historical_prices(limit=200)` | ~30 KB |
| `equity_intraday_prices(limit=70)` | ~15 KB |

None of these hit the opencode runtime's truncation threshold (~256 KB). Safe to include in multi-call batches.

## Coverage flags

`meta.coverage_status` is typically `full` for liquid pairs/tickers. For delisted or newly-listed names it may be `partial`. Always cite `time` (snapshot) or `as_of_date` (history).

## See also

- `llmquant-funds` — for ETF price proxies (e.g. SPY) and constituent-level exposure
- `llmquant-macro` — for risk-free rate / CPI overlay on equity returns
- `llmquant-personal` — combine with the user's saved portfolio to compute mark-to-market