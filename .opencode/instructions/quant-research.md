# Quantitative Research Instructions

> **Vendored from Vibe-Trading v0.1.15 — "data that says what it is"**
> (2026-09-09). The vendored `vibe-trading-ai` package now tracks this
> version. Key upstream changes affecting research output: NaN contract
> enforced at the alpha registry, `pct_change()` no longer forward-fills,
> adjustment caliber stamped on price frames, futures chain moved to
> `["akshare", "local"]`, three new markets added (UK equity, KRX, Vietnam).

## Scope

This instruction governs the use of `vibe-trading-ai` — the vendored quantitative engine providing backtest engines, data loaders, alpha zoo, portfolio optimizers, swarm presets, and multi-market analysis skills.

## Data Source Routing

When a `vibe-trading-ai` data loader is invoked, follow the per-market fallback chain:

### A-Share
1. MooTDX (通达信 TCP, never banned)
2. Tencent / Sina (HTTP lightweight)
3. Baostock (free, reliable)
4. AKShare / EastMoney (feature-rich)
5. Tushare (token-gated, high quality)

### US / Global Equities
1. Yahoo Finance (Stooq fallback — anti-bot challenge is flagged, not parsed)
2. EastMoney (also covers HK)
3. Finnhub / Alpha Vantage / Tiingo / FMP (token-gated; named explicitly — never silently degrades)

### HK Equities
1. Tencent (never banned)
2. EastMoney / Yahoo
3. LongBridge (`LONGBRIDGE_*` token-gated, SDK)

### Canada Equities (TSX .TO / TSXV .V)
1. Yahoo Finance (`<TICKER>.TO` / `<TICKER>.V`)

### India Equities
1. Yahoo Finance (`.NS` / `.BO` suffixes)
2. India broker loaders (Shoonya / Dhan — read-only live; no paper/live discriminator means live order placement is structurally disabled)

### Korea Equities (KRX: KOSPI .KS / KOSDAQ .KQ)
1. pykrx (Naver-adjusted daily; `pip install "vibe-trading-ai[krx]"`)
2. Yahoo Finance (fallback)

### Vietnam Equities (HOSE .VN)
1. Yahoo Finance (`<TICKER>.VN`) — HNX/UPCOM venues unsupported; long-only, ±7% band, 100-share lots.

### UK Equities (LSE .L / .IL) — new in v0.1.15
1. Yahoo Finance (`.L` / `.IL`)
   SDRT: 0.5% stamp duty on the **purchase side only**, not symmetric round-trip.

### Crypto
1. OKX (spot)
2. CCXT (100+ exchanges aggregated)
3. Nobitex / Wallex (Iranian Toman — **explicit-only**, never joins fallback chain)

### China Futures
1. **AKShare** (Sina daily endpoints, dated + main continuous, SHFE/CFFEX/GFEX/ZCE)
2. `local` (offline CSV/parquet)
   > tushare no longer declares `futures` (its `pro.fut_daily` is points-tier).

### Global Futures / Forex / Metals
1. Yahoo Finance
2. AKShare
3. MT5 (local terminal)
4. **TickerAll** (hosted MT5 HTTP API, `TICKERALL_API_KEY` + `TICKERALL_ACCOUNT_ID` — **explicit-only**)

### SEC Filings
Use dedicated SEC EDGAR client via `vibe-trading-ai.loaders.sec_edgar_client`

## Alpha Zoo Research

The **462** pre-built alphas are organized (count rose from 461 in v0.1.15):
- **qlib158**: Quantitative research alphas (158) — tagged for `equity_cn`, `equity_in`, `equity_kr`
- **alpha101**: 101 formulaic alphas (subset used by qlib)
- **gtja191**: GTJA 191 alphas (China-specific, `equity_cn` only)
- **academic**: Academic research alphas
- **fundamental**: Fundamental factor alphas

**Rules (v0.1.15 tightened):**
- Alpha bench is for research and comparison only
- IC/IR analysis must use a proper train/test split (no lookahead bias)
- **NaN is preserved through warm-up and missing data** — no silent `fillna(0)`. An
  alpha whose declared input is missing on a bar must emit NaN; cite the
  sample size after the drop, never the fabricated number.
- **`pct_change()` does not forward-fill by default** — a missing close is a
  missing return, not `0.0%`. Multi-factor TopN selection now excludes
  assets with no factor observations rather than ranking them at zero.
- **Survivorship-bias flag** must be rendered in the bench HTML and quoted
  when citing IC numbers — a caveat in the data only is the same failure mode
  one level up.
- Never present backtest results as expected future returns
- Always flag PIT (Point-in-Time) data violations
- When using swarm presets, ensure no trading-related nodes are invoked

## Backtest Discipline (new in v0.1.15)

- **Data window separated from evaluation window** — warm-up bars stop
  counting as evaluation; a strategy is no longer graded on the bars it
  needed to become defined.
- **Adjustment caliber** (`split_adjusted` / `dividend_adjusted` / `raw` /
  `unknown`) is stamped on the served frame; cite it next to any cited price.
- **Intraday fundamentals are refused by default** — an announcement date
  carries no time of day, so on an intraday frame a filing would otherwise
  be visible from the first bar of its own announcement day (full session
  of lookahead). Sub-daily frames must opt in via
  `fundamental_subdaily="next_day"`.
- **Options fills on next bar**, not the date the signal was computed from —
  HV warm-up uses the configured default IV; short option legs hold margin
  and gate opens on buying power; explicit expirations validated against
  the dates actually available rather than silently resolved to a neighbour.
- **Read-only multi-broker portfolio aggregation** — `portfolio_summary`
  tool aggregates across enabled broker connections; a source that fails to
  refresh is an **error excluded from totals** (never a carried-forward
  cache). Use this in preference to single-source views.

## No Live Trading

This repository is explicitly **NOT** a trading system. No subagent, skill, or script should:
- Place orders through any broker API
- Connect to real-time market feeds for execution
- Authorize fund transfers or portfolio rebalancing outside of draft proposals
- Execute any action that would result in financial transaction

Violations should be reported as bugs.
