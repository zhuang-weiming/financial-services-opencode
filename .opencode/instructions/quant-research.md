# Quantitative Research Instructions

## Scope

This instruction governs the use of `vibe-trading-quanta` — the vendored quantitative engine providing backtest engines, data loaders, alpha zoo, portfolio optimizers, swarm presets, and multi-market analysis skills.

## Data Source Routing

When a `vibe-trading-quanta` data loader is invoked, follow the per-market fallback chain:

### A-Share
1. MooTDX (通达信 TCP, never banned)
2. Tencent / Sina (HTTP lightweight)
3. Baostock (free, reliable)
4. AKShare / EastMoney (feature-rich)
5. Tushare (token-gated, high quality)

### US / Global Equities
1. Yahoo Finance (Stooq fallback)
2. EastMoney (also covers HK)
3. Finnhub / Alpha Vantage / FMP (token-gated)

### Crypto
1. OKX
2. CCXT (100+ exchanges aggregated)

### India Equities
1. Yahoo Finance (`.NS` / `.BO` suffixes)
2. India broker loaders (Shoonya / Dhan — read-only)

### SEC Filings
Use dedicated SEC EDGAR client via `vibe-trading-quanta.loaders.sec_edgar_client`

## Alpha Zoo Research

The 461 pre-built alphas are organized:
- **qlib158**: Quantitative research alphas (158)
- **alpha101**: 101 formulaic alphas
- **gtja191**: GTJA 191 alphas (China-specific)
- **academic**: Academic research alphas
- **fundamental**: Fundamental factor alphas

**Rules:**
- Alpha bench is for research and comparison only
- IC/IR analysis must use a proper train/test split (no lookahead bias)
- Never present backtest results as expected future returns
- Always flag PIT (Point-in-Time) data violations
- When using swarm presets, ensure no trading-related nodes are invoked

## No Live Trading

This repository is explicitly **NOT** a trading system. No subagent, skill, or script should:
- Place orders through any broker API
- Connect to real-time market feeds for execution
- Authorize fund transfers or portfolio rebalancing outside of draft proposals
- Execute any action that would result in financial transaction

Violations should be reported as bugs.
