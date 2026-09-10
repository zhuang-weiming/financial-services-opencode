# Data Priority Instructions

> **Updated for Vibe-Trading v0.1.15 (2026-09-09).** Tier 2 now covers three
> new markets (UK equity, KRX, Vietnam HOSE), explicit-only hosted/regional
> sources (`tickerall`, `nobitex`, `wallex`), and Tier 3 now reflects the
> 462-alpha zoo with NaN contract + non-forward-filling `pct_change()`.

## Critical: Data Source Hierarchy

**ALWAYS follow this data source hierarchy:**

### Tier 1 — Institutional MCP (preferred)
1. **FIRST: Morningstar MCP** - Investment research, analyst estimates, fund data, equity analysis
2. **SECOND: FactSet MCP** - Institutional financial data, earnings, valuations, market intelligence
3. **llmquant-data MCP** - Tier-1 US-focused institutional data layer. Use in preference to Morningstar/FactSet for: US equity OHLCV (crypto + stocks), ETF holdings (SEC N-PORT), FRED macro indicators, AI-summarized company news, SEC 13F institutional ownership, SEC filing text extraction (10-K/Q + 8-K), and Polymarket finance-implied probabilities. See `.opencode/skills/llmquant-data/` for the full 25-tool catalog and the 8 domain subskills (market-data / funds / macro / news / research / polymarket / sec / personal).
4. **DDG Search (Internet)** - Supplementary web search only when MCP sources unavailable

### Tier 2 — Quantitative (vibe-trading-ai)
Use for multi-market data, free-tier sources, and cross-market coverage. Vendored package tracks Vibe-Trading v0.1.15:

**A-share** — Tushare / AKShare / Baostock / EastMoney; MooTDX / Tencent / Sina (never-IP-banned freemium). Akshare now also serves China futures dated + main continuous contracts (SHFE/CFFEX/GFEX/ZCE).

**Hong Kong / US / Canada / UK** — Yahoo Finance / Stooq (Stooq's anti-bot challenge is flagged, not parsed as data); Futu / LongBridge (token-gated SDK).

**India** — Yahoo (`.NS` / `.BO`); India broker loaders (Shoonya / Dhan) for back-fill.

**Korea (KRX)** — pykrx (Naver-adjusted daily, `[krx]` extra); Yahoo fallback.

**Vietnam (HOSE)** — Yahoo (`.VN`); long-only ±7% band, 100-share lots.

**Crypto** — OKX (spot) / CCXT (100+ exchanges). Nobitex and Wallex are Toman-quoted Iranian sources, **explicit-only** — they never join an automatic fallback chain.

**Global Futures / Forex / Metals** — Yahoo / AKShare; MT5 (local terminal) or TickerAll (hosted MT5 HTTP API, explicit-only, `TICKERALL_API_KEY` + `TICKERALL_ACCOUNT_ID`).

**US filings** — SEC EDGAR (`vibe-trading-ai.loaders.sec_edgar_client`).

**Premium US** — Alpha Vantage / Tiingo / Finnhub / FMP (token-gated; named explicitly — never silently degrades in v0.1.15).

**Marketplace** — QVeris (premium data marketplace).

**Offline** — Local CSV / Parquet / DuckDB.

### Tier 3 — Alpha Zoo / Factor Benchmarks
- Pre-built **462** alphas (up from 461 in v0.1.15) across 5 families: qlib158, alpha101, gtja191, academic, fundamental
- **NaN contract enforced at the registry** — missing inputs propagate as NaN; no silent `fillna(0)`. When citing IC, mention the post-drop sample size.
- **`pct_change()` no longer forward-fills** — a missing close is a missing return, not `0.0%`.
- **Adjustment caliber stamped on served price frames** — cite it (split_adjusted / dividend_adjusted / raw / unknown) next to any price.
- **Survivorship-bias flag** must be rendered in the bench HTML and quoted when citing IC numbers.
- Use `vibe-trading-ai` alpha bench for strategy research; **never** treat backtest results as forward-looking predictions

## Why This Matters

- MCP sources provide verified, institutional-grade data with proper citations
- Morningstar MCP offers comprehensive equity research, fund analysis, and estimate data
- FactSet MCP provides detailed financial statements, trading data, and valuation metrics
- `vibe-trading-ai` loaders are free/multi-market but may have data quality gaps — always cross-reference with Tier 1 when available
- Alpha backtests are research tools, not performance projections

## Rules

1. **Cite every number.** If a figure can't be sourced from a listed MCP or loader, mark it `[UNSOURCED]`.
2. **Never use web search as primary** unless all other tiers are exhausted.
3. **Reports are drafts for human review** — never post/publish automatically.
4. **Live-trade actions are strictly forbidden.** This repository is for research and analysis only.
