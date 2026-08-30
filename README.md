# Opencode for Financial Services (Wealth-Guide)

A unified financial-services AI agent platform powered by [Opencode](https://opencode.ai). Single-entry agent **Wealth-Guide** routes your question to the right specialized subagent — covering investment banking, equity research, private equity, wealth management, fund administration, and multi-market quantitative research.

## Provenance

This repository merges two open-source codebases:

| Source | License | Version | Contents |
|---|---|---|---|
| [Anthropic FSI](https://github.com/anthropic/claude-for-financial-services) | Apache 2.0 | — | 17 subagents, 59 institutional FSI skills, 3 MCP data connectors |
| [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | MIT | v0.1.11 | Multi-market analysis & quantitative research: 87 skills, 461 alpha zoo, 11 backtest engines, 21+ data loaders, 30 swarm presets, 6 portfolio optimizers |
| [LLMQuant/skills](https://github.com/LLMQuant/skills) | MIT | v0.1.0 | 17 workflow-router category skills (75 workflows) grounded in LLMQuant Data (options, credit, rates-fx, crypto, commodities, strategies, investor-lenses, and more) |

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url> financial-services-opencode
cd financial-services-opencode

# 2. Install Python dependencies
pip install -r .opencode/requirements.txt

# 3. Install vendored quant engine (optional — only for backtest/alpha/data-loader features)
pip install -e .opencode/python/vibe-trading-quanta

# 4. Install Node.js plugin dependencies (optional — required for Opencode plugin)
cd .opencode && npm install && cd ..

# 5. Start a session with Wealth-Guide
opencode --agent wealth-guide
```

> **Note:** Steps 2–3 are required for Python-based features (xlsx creation, backtesting, alpha research, data loaders). Step 4 is only needed if you use this as an Opencode plugin via `opencode plugin install`.

## Setup Details

### Python Dependencies

The `.opencode/requirements.txt` covers all core dependencies:

| Package | Used By |
|---|---|
| `openpyxl` | xlsx/xlsx-author skills (Excel creation) |
| `python-pptx` | pptx/pptx-author skills (PowerPoint creation) |
| `pandas`, `numpy` | Data manipulation across all quant skills |
| `scipy`, `scikit-learn`, `statsmodels` | Alpha research, factor analysis, backtesting |
| `duckdb`, `pyarrow` | Data storage and query |
| `httpx`, `requests` | Web data fetching |
| `Pillow` | Image processing for doc-reader |
| `mcp` | MCP server communication |

Optional data-loader packages (uncomment in `requirements.txt` or install as needed):

```bash
pip install tushare yfinance akshare ccxt finnhub-python
```

### Node.js Dependencies

If using as an Opencode plugin:

```bash
cd .opencode && npm install
```

This installs `@opencode-ai/plugin` (the Opencode plugin runtime).

## Architecture

```
                           ┌──────────────────────┐
                           │     wealth-guide      │  ← ONLY user-facing entry
                           │ (intent → delegate)   │
                           └──────┬───────────────┘
                                  │ task(subagent=...)
          ┌───────────────────────┼────────────────────────┐
          │       (22 subagents)  │                        │
       IB/ER/PE/WM           Modeling                Fund-Admin
       pitch-agent            model-builder          gl-reconciler
       earnings-reviewer      alpha-researcher       month-end-closer
       market-researcher      backtest-builder       statement-auditor
       meeting-prep-agent     factor-researcher      kyc-screener
       ...                    market-router          ...
                               swarm-orchestrator
```

- **1 primary agent** (`wealth-guide`): single entry point, no user-facing agent explosion
- **22 subagents**: each good at one domain, hidden from the user
- **180 skills**: reusable workflow procedures triggered by subagents — incl. 17 `llmquant-*` workflow routers (75 workflows) + 9 `llmquant-data` tool-reference skills
- **`vibe-trading-quanta` Python package**: vendored quantitative engine (backtest, alpha zoo, data loaders, swarm presets, portfolio optimizers)

## Subagent Reference

| Subagent | Domain | Key Capabilities |
|---|---|---|
| `investment-banking` | IB | Pitch decks, CIMs, teasers, buyer lists, merger models, deal tracking |
| `pitch-agent` | IB (specialized) | Buy-side pitch decks, comps, DCF, LBO, football field |
| `equity-research` | ER | Earnings analysis, initiating coverage, morning notes, thesis tracking |
| `earnings-reviewer` | ER (specialized) | Post-earnings update: transcript → model → note |
| `market-researcher` | ER (specialized) | Sector primers, competitive landscapes, idea generation |
| `private-equity` | PE | IC memos, deal screening/sourcing, unit economics, returns analysis |
| `operations` | PE ops | Portfolio monitoring, AI readiness, DD checklists, value creation |
| `wealth-management` | WM | Financial plans, portfolio rebalancing, TLH, client reports |
| `meeting-prep-agent` | WM (specialized) | Client/investor meeting prep packs |
| `model-builder` | Modeling | DCF, LBO, 3-statement, comps from scratch |
| `financial-analysis` | Cross-domain | 3-statement, DCF, LBO, comps, competitive analysis |
| `alpha-researcher` | Quant research | Alpha zoo browse, IC/IR, factor bench, strategy research |
| `factor-researcher` | Factor analysis | IC/IR, quantile backtest, correlation, risk decomposition |
| `backtest-builder` | Strategy dev | Strategy generation, backtesting, walk-forward, diagnosis |
| `market-router` | Cross-market | Multi-market data routing (A-share, US, crypto, FX, futures) |
| `swarm-orchestrator` | Multi-agent | 30 preset research teams and collaborative workflows |
| `fund-admin` | Fund admin | NAV tie-out, accruals, roll-forwards, variance commentary |
| `gl-reconciler` | Fund GL | GL reconciliation, break classification, root-cause trace |
| `month-end-closer` | Month-end | Accrual schedules, roll-forwards, close packages |
| `statement-auditor` | LP audit | NAV tie-out, formula audit, cross-statement consistency |
| `kyc-screener` | KYC/AML | Onboarding document parse, AML rules engine, risk rating |
| `valuation-reviewer` | Valuation QA | Assumption stress-test, sensitivity analysis, model challenge |

## Data Sources

### Tier 1 — Institutional (preferred)
- **Morningstar MCP**: equity research, analyst estimates, fund data, fair value estimates
- **FactSet MCP**: financial statements, trading data, valuation metrics
- **llmquant-data MCP**: US equity/crypto OHLCV, ETF holdings (SEC N-PORT), FRED macro indicators, AI-summarized news, SEC 13F ownership, SEC filing text (10-K/Q + 8-K), Polymarket finance odds, papers/wiki knowledge (25 tools, 8 domains)

### Tier 2 — General Web (fallback)
- **DuckDuckGo Search**: supplementary web search when MCP sources unavailable

### Tier 3 — Quantitative (free/multi-market)
All routed through `vibe-trading-quanta` data loaders:
- **A-Share**: MooTDX (通达信 TCP), Tencent, Sina, Baostock, AKShare, EastMoney, Tushare
- **US/Global**: Yahoo Finance, Stooq, EastMoney, Finnhub, Alpha Vantage, Financial Modeling Prep
- **Crypto**: OKX, CCXT (100+ exchanges)
- **India**: Yahoo Finance (.NS/.BO), broker loaders
- **SEC Filings**: SEC EDGAR client via `vibe-trading-quanta.loaders.sec_edgar_client`

> **Data quality priority** is enforced by the `.opencode/instructions/data-priority.md` rule — always prefer MCP sources over free loaders, and mark any unsourced figure with `[UNSOURCED]`.

## Alpha Zoo (461 pre-built factors)

Five families bundled in `vibe-trading-quanta`:

| Family | Count | Origin |
|---|---|---|
| `qlib158` | 158 | Microsoft Qlib quantitative alphas |
| `alpha101` | 101 | Kakushadze 101 formulaic alphas |
| `gtja191` | 191 | GTJA (国泰君安) China-specific alphas |
| `academic` | — | Academic research alphas (Fama-French, Carhart, etc.) |
| `fundamental` | — | Fundamental factor alphas |

```python
from vibe_trading_quanta.factors.registry import Registry
zoo = Registry.get_alpha("qlib158")  # loads all 158 Qlib alphas
```

## LLMQuant Workflow Skills

17 workflow-router category skills imported from [`LLMQuant/skills`](https://github.com/LLMQuant/skills) (MIT), grounded in the `llmquant-data` MCP. Each router indexes `workflows/*.md` procedures and enforces the LLMQuant Data evidence contract (source grounding, freshness reporting, fallback, no invented data). See `.opencode/instructions/llmquant-skills.md` for the full category → scenario → trigger → subagent map and the legacy-skill cross-reference matrix.

| Skill | Category | Workflows | Primary subagent(s) |
|---|---|---:|---|
| `llmquant-options` | options | 10 | `factor-researcher` / `financial-analysis` |
| `llmquant-investor-lenses` | investor-lenses | 17 | `equity-research` / `wealth-management` |
| `llmquant-strategies` | strategies | 6 | `backtest-builder` / `swarm-orchestrator` |
| `llmquant-equities` | equities | 5 | `equity-research` / `earnings-reviewer` |
| `llmquant-portfolio` | portfolio | 5 | `wealth-management` / `equity-research` |
| `llmquant-risk` | risk | 4 | `valuation-reviewer` / `factor-researcher` |
| `llmquant-credit` | credit | 3 | `financial-analysis` / `market-researcher` |
| `llmquant-crypto` | crypto | 3 | `market-router` / `factor-researcher` |
| `llmquant-events` | events | 3 | `earnings-reviewer` / `market-researcher` |
| `llmquant-macro` | macro | 3 | `market-router` / `factor-researcher` / `wealth-management` |
| `llmquant-market-intelligence` | market-intelligence | 3 | `market-researcher` / `equity-research` |
| `llmquant-prediction-markets` | prediction-markets | 3 | `market-researcher` / `market-router` |
| `llmquant-rates-fx` | rates-fx | 3 | `market-router` / `factor-researcher` |
| `llmquant-commodities` | commodities | 2 | `market-researcher` / `market-router` |
| `llmquant-equity-derivatives` | equity-derivatives | 2 | `financial-analysis` / `factor-researcher` |
| `llmquant-portfolio-lab` | portfolio-lab | 2 | `wealth-management` / `valuation-reviewer` |
| `llmquant-etfs` | etfs | 1 | `market-researcher` / `financial-analysis` |

**Total**: 17 routers, 75 workflows. 16 shipped as-is; `llmquant-macro` merged into the existing tool-reference macro skill; `llmquant-strategies` (voice/tone) and `llmquant-investor-lenses` (persona grounding) shipped with integration notes.

## Changelog

### v1.5 — 2026-08-29
**LLMQuant integration**: 17 new workflow-router category skills (75 workflows, `LLMQuant/skills` v0.1.0) + `llmquant-data` MCP (25 tools, 8 domains) wired into the agent's tool list. New `.opencode/instructions/llmquant-skills.md` registry doc (category → scenario → trigger → subagent mapping, legacy-skill cross-reference). 9 legacy skills updated with "Related llmquant skills" cross-refs. Wealth-Guide upgraded with `mcp__llmquant-data__*` tool wiring and `> Version 1.5` marker.
- **+16 new skill folders** (commodities, credit, crypto, equities, equity-derivatives, etfs, events, investor-lenses, market-intelligence, options, portfolio, portfolio-lab, prediction-markets, rates-fx, risk, strategies)
- **+3 workflows merged** into existing `llmquant-macro` (global-macro-dashboard, fed-policy-preview, macro-to-portfolio-impact)
- **+9 tool-ref skills** from the prior turn (data master + market-data, funds, macro, news, research, polymarket, sec, personal)
- **+28 Skill Registry rows** in `wealth-guide-router.md`
- **README** Provenance table extended; Data Sources Tier 1 adds `llmquant-data MCP`; new "LLMQuant Workflow Skills" section; skill count 146 → **180**

### v1.0 — initial versioned release
First explicit Wealth-Guide version. Baseline = Anthropic FSI (17 subagents, 59 institutional skills, 3 MCP data connectors) + Vibe-Trading (87 skills, 461 alpha zoo, 11 backtest engines, 21+ data loaders, 30 swarm presets, 6 portfolio optimizers) + 22 subagents total.

---

## MCP Configuration

The repo includes MCP server config at `.opencode/mcp/servers.json` for Morningstar, FactSet, and llmquant-data. To use these, you need your own API keys:

```bash
# Set environment variables before starting opencode
export MORNINGSTAR_API_KEY="your-key"
export FACTSET_API_KEY="your-key"
export LLMQUANT_API_KEY="your-key"
```

Without MCP keys, the system falls back to Tier 2 (DDG search) and Tier 3 (free quant loaders).

## Cookbooks (`./example/`)

Each subagent has a cookbook with sample data files and question sets. These serve as tutorials and test cases:

```bash
# Try a cookbook
opencode --agent wealth-guide --prompt "$(cat example/earnings-reviewer/questions.md)"
```

Available cookbooks:
- `example/wealth-guide-e2e/` — End-to-end walkthrough
- `example/explore/` — Introduction to using wealth-guide
- `example/<subagent-name>/` — One per subagent (22 total)

## Testing

```bash
# Run the full test suite
python tests/run_all.py
```

The test suite covers:
- **Structural tests**: agent frontmatter, skill/instruction validity, frontmatter integrity
- **Integration tests**: alpha Registry loading, live-trade pattern detection, MCP integrity, skill syntax checks
- **Business acceptance**: Chinese queries, multi-domain routing, cross-contamination (adversarial queries), edge cases, routing table coverage
- **Unit tests**: routing logic, pipeline correctness

## License

This project contains work from multiple sources:
- Original Anthropic FSI content: Apache 2.0
- Vibe-Trading content (vendored as `vibe-trading-quanta`): MIT — see `.opencode/python/vibe-trading-quanta/.LICENSE_VIBE_TRADING`
- Merged original code: Apache 2.0

---

**This repository is for research and analysis only. No live trading or order execution is permitted.**
