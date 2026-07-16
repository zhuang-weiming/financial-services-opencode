# Data Priority Instructions

## Critical: Data Source Hierarchy

**ALWAYS follow this data source hierarchy:**

### Tier 1 — Institutional MCP (preferred)
1. **FIRST: Morningstar MCP** - Investment research, analyst estimates, fund data, equity analysis
2. **SECOND: FactSet MCP** - Institutional financial data, earnings, valuations, market intelligence
3. **THIRD: DDG Search (Internet)** - Supplementary web search only when MCP sources unavailable

### Tier 2 — Quantitative (vibe-trading-quanta)
Use for multi-market data, free-tier sources, and cross-market coverage (A-share, crypto, forex, futures, India):
- Tushare / AKShare / Baostock (A-share)
- MooTDX / Tencent / Sina (A-share, never-IP-banned freemium)
- EastMoney (A-share + HK)
- Yahoo Finance / Stooq (global equities)
- OKX / CCXT (crypto)
- SEC EDGAR (US filings)
- Futu / LongBridge (HK/US via SDK)
- Alpha Vantage / Tiingo / Finnhub / FMP (premium US)
- QVeris (premium data marketplace)
- Local CSV / Parquet / DuckDB

### Tier 3 — Alpha Zoo / Factor Benchmarks
- Pre-built 461 alphas across 5 families: qlib158, alpha101, gtja191, academic, fundamental
- Use `vibe-trading-quanta` alpha bench for strategy research; **never** treat backtest results as forward-looking predictions

## Why This Matters

- MCP sources provide verified, institutional-grade data with proper citations
- Morningstar MCP offers comprehensive equity research, fund analysis, and estimate data
- FactSet MCP provides detailed financial statements, trading data, and valuation metrics
- `vibe-trading-quanta` loaders are free/multi-market but may have data quality gaps — always cross-reference with Tier 1 when available
- Alpha backtests are research tools, not performance projections

## Rules

1. **Cite every number.** If a figure can't be sourced from a listed MCP or loader, mark it `[UNSOURCED]`.
2. **Never use web search as primary** unless all other tiers are exhausted.
3. **Reports are drafts for human review** — never post/publish automatically.
4. **Live-trade actions are strictly forbidden.** This repository is for research and analysis only.
