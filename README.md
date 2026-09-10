# Opencode for Financial Services (Wealth-Guide)

A unified financial-services AI agent platform powered by [Opencode](https://opencode.ai). Single-entry agent **Wealth-Guide** routes your question to the right specialized subagent — covering investment banking, equity research, private equity, wealth management, fund administration, and multi-market quantitative research.

## Provenance

This repository merges two open-source codebases:

| Source | License | Version | Contents |
|---|---|---|---|
| [Anthropic FSI](https://github.com/anthropic/claude-for-financial-services) | Apache 2.0 | — | 17 subagents, 59 institutional FSI skills, 3 MCP data connectors |
| [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | MIT | v0.1.15 | Multi-market analysis & quantitative research ("data that says what it is"): 90 skills, 462 alpha zoo, 10 backtest engines, 27 data loaders (incl. UK / KRX / HOSE markets, tickerall / nobitex / wallex explicit-only sources, pykrx KRX), 30 swarm presets, 6 portfolio optimizers, 14 broker connectors, 74 MCP tools |
| [LLMQuant/skills](https://github.com/LLMQuant/skills) | MIT | v0.1.0 | 17 workflow-router category skills (75 workflows) grounded in LLMQuant Data (options, credit, rates-fx, crypto, commodities, strategies, investor-lenses, and more) |

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url> financial-services-opencode
cd financial-services-opencode

# 2. One-shot Python setup (deps + vendored packages, editable install)
pip install -r .opencode/requirements.txt
pip install -e .opencode/python/vibe-trading
pip install -e .opencode/python/wif-framework

# 3. Install Node.js plugin dependencies (optional — required for Opencode plugin)
cd .opencode && npm install && cd ..

# 4. Start a session with Wealth-Guide
opencode --agent wealth-guide
```

> **Note:** Steps 2–3 are a **one-time setup** — after that, the agent runs with
> zero install delay. The two vendored Python packages are installed *editable*
> (`vibe-trading-ai` v0.1.15 from `.opencode/python/vibe-trading`, and
> `wif-framework` v5.9.0 from `.opencode/python/wif-framework`), and the
> data-loader extras (tushare / yfinance / akshare / pykrx / mootdx / baostock)
> are already resolved. Step 3 is only needed if you use this as an Opencode
> plugin via `opencode plugin install`.


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
- **183 skills**: reusable workflow procedures triggered by subagents — **89 `vibe-trading-*`** (Vibe-Trading origin, v0.1.15) + 25 `llmquant-*` + 9 `llmquant-data` tool-reference skills + Anthropic FSI institutional skills. Naming convention: `vibe-trading-*` = vendored from HKUDS/Vibe-Trading; `llmquant-*` = imported from LLMQuant/skills; bare names = Anthropic FSI or repo-local.
- **`vibe-trading-ai` Python package** (v0.1.15, installed from `.opencode/python/vibe-trading`): vendored quantitative engine + agent tree — 462 alphas with NaN contract, 27 data loaders, 10 backtest engines, swarm presets, portfolio optimizers, plus the Quant Library (`src.quantlib.*`), tools (`src.tools.*`), factors (`src.factors.*`), and trading connectors. Namespace: `src.*` / `backtest.*` / `cli.*` (e.g. `from src.quantlib.timeseries import adf_test`, `from backtest.loaders.registry import VALID_SOURCES`).
- **`vibe-trading` MCP server**: optional, started by `vibe-trading-mcp` (74 tools from the upstream engine). Note: the MCP's `load_skill` resolves against the package's own bundled skills (`src/skills/`, bare names) — a *separate* corpus from the renamed `.opencode/skills/vibe-trading-*` that OpenCode agents use.

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
| `market-router` | Cross-market | Multi-market data routing (A-share, US, crypto, FX, futures, India, Korea, Vietnam, UK, Canada; explicit-only tickerall/nobitex/wallex) |
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
All routed through `vibe-trading-ai` data loaders (v0.1.15):
- **A-Share**: MooTDX (通达信 TCP), Tencent, Sina, Baostock, AKShare, EastMoney, Tushare
- **US/Global**: Yahoo Finance, Stooq, EastMoney, Finnhub, Alpha Vantage, Tiingo, Financial Modeling Prep
- **HK**: Tencent, EastMoney, Yahoo, LongBridge (SDK), Futu (OpenD)
- **Canada**: Yahoo (.TO / .V)
- **India**: Yahoo (.NS / .BO), broker loaders (Shoonya / Dhan); live order placement disabled
- **Korea (KRX)**: pykrx (Naver-adjusted daily); Yahoo fallback
- **Vietnam (HOSE)**: Yahoo (.VN); long-only, ±7% band
- **UK (LSE)**: Yahoo (.L / .IL); SDRT 0.5% purchase-side duty
- **Crypto**: OKX, CCXT (100+ exchanges); nobitex / wallex Toman sources are explicit-only
- **China Futures**: AKShare (Sina daily endpoints); tushare no longer declares `futures`
- **Global Futures / Forex / Metals**: Yahoo, AKShare, MT5 (local), TickerAll (hosted MT5, explicit-only)
- **SEC Filings**: SEC EDGAR client via `backtest.loaders.sec_edgar_client`

> **Data quality priority** is enforced by the `.opencode/instructions/data-priority.md` rule — always prefer MCP sources over free loaders, and mark any unsourced figure with `[UNSOURCED]`.
>
> **v0.1.15 data integrity rules**: every served price frame carries an
> adjustment caliber (`split_adjusted` / `dividend_adjusted` / `raw` / `unknown`);
> cite it next to any price you quote. NaN propagates through the alpha zoo
> instead of being silently filled — quote IC values with the post-drop
> sample size. `pct_change()` does not forward-fill — a missing close is a
> missing return.

## Alpha Zoo (462 pre-built factors)

Five families bundled in the `vibe-trading-ai` package (v0.1.15 — grew from 461):

| Family | Count | Origin |
|---|---|---|
| `qlib158` | 158 | Microsoft Qlib quantitative alphas (tagged `equity_cn`, `equity_in`, `equity_kr`) |
| `alpha101` | 101 | Kakushadze 101 formulaic alphas |
| `gtja191` | 191 | GTJA (国泰君安) China-specific alphas (`equity_cn` only) |
| `academic` | — | Academic research alphas (Fama-French, Carhart, etc.) |
| `fundamental` | — | Fundamental factor alphas |

```python
from src.factors.registry import Registry
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

### v1.7 — 2026-09-10 (Vibe-Trading skill namespace)
**Renamed all 89 Vibe-Trading-origin skills to the `vibe-trading-*` namespace**, giving provenance symmetry with the `llmquant-*` skills imported from LLMQuant/skills. Also removed the redundant `vibe-thesis-tracker` duplicate.
- **89 skills renamed** `X` → `vibe-trading-X` (directory + `name:` frontmatter). `thesis-tracker` was left bare — it is Anthropic/legacy origin (added 2026-05-26), and the Vibe-Trading duplicate `vibe-thesis-tracker` was deleted, with its 2 references repointed to `thesis-tracker`
- **References updated**: 275 markdown links, 146 backtick refs, 4 bold refs, agent Key-Skills tables, router Skill Registry, `llmquant-skills.md` cross-reference matrix, 8 `references/`/`scripts/` path refs, README, `opencode.json`, and test fixtures (`SKILLS_DIR / "…"`)
- **Two independent skill systems clarified**: the active OpenCode skills (`.opencode/skills/`, renamed) vs the vendored package's bundled skills (`.opencode/python/vibe-trading/src/skills/`, upstream bare names, loaded by the package's own `load_skill`). Swarm-preset `skill()` calls were reverted to bare names so the vendored packages stay self-consistent with their own `src/skills/`
- **Verified**: 0 broken skill refs, 0 broken links, all 89 frontmatter names match directories, `skill()` calls resolve; full test suite unchanged at 1327 passed / 2 pre-existing failures (memory-file naming + BT directory structure, both unrelated)

### v1.6.1 — 2026-09-10 (re-merge audit)
**Full re-merge of the vendored Vibe-Trading trees.** An audit found the merge was fragmented and stale: `.opencode/python/vibe-trading/` was still at **v0.1.13** (52 `src/` + 8 `backtest/` + 1 `cli/` files missing, 148 `src/` files outdated, `mcp_server.py` 4 tools short) while only `vibe-trading-ai` had been bumped to v0.1.15. Additionally a prior fix had uninstalled `vibe-trading-ai`, breaking the `src.*` / `backtest.*` / `cli.*` imports that ~40 skills depend on.
- **`.opencode/python/vibe-trading/`** — rsync'd to upstream v0.1.15; custom `pyproject.toml` preserved and bumped 0.1.13 → **0.1.15**; reinstalled. Now: src 908/908, backtest 83/83, cli 43/43, src/skills 90/90, src/tools 78/78, quantlib 19/19
- **New v0.1.15 modules restored**: `src/quantlib/{copula,microstructure,portfolio,volatility}.py`, `src/portfolio/*` (8), `src/trading/connectors/zerodha/*` (4), `src/strategy_discovery/*` (8), `src/scheduled_research/*` (3), `src/tools/{portfolio,strategy_discovery,scheduled_research}_tool.py`, `backtest/engines/vietnam_equity.py`, `backtest/loaders/{pykrx,tickerall,mt5,nobitex,wallex}`, `cli/commands/strategy_evidence.py`
- **Skills**: added 2 missing skills (`vibe-trading-investor-lenses`, `vibe-trading-strategy-discovery`) + 17 missing files (16 `example_signal_engine.py` + `vibe-trading-strategy-generate/examples.md`); content-synced **37 skills** to v0.1.15 (headline: `pct_change()` → `pct_change(fill_method=None)` across 6 skills; Quant Library "import, don't retype" sections across 6 skills; naming/units/API corrections in 9 more)
- **Verified**: both packages import at 0.1.15; 18 skill-referenced modules resolve; quanta registry intact at 27 loaders with no cross-contamination

### v1.6 — 2026-09-10
**Vibe-Trading v0.1.15 sync** ("data that says what it is"). The vendored
`vibe-trading-ai` package and Tier-2 routing now reflect: **462 alpha zoo**
(was 461, NaN contract enforced at the registry), `pct_change()` no longer
forward-fills, adjustment caliber stamped on served price frames, three new
markets (**UK equity / Korea KRX / Vietnam HOSE**), explicit-only sources
(`tickerall` hosted MT5, `nobitex`/`wallex` Iranian Toman), 14 broker
connectors (Zerodha Kite added; live order placement structurally disabled
because Kite has no paper/live switch). New `vibe-trading` MCP server entry
in `opencode.json` (74 upstream tools).
- **`vibe-trading-ai`** — package version 0.1.0 → **0.1.15**, `__source__`
  bumped to Vibe-Trading v0.1.15
- **`alpha-zoo/SKILL.md`** — 461 → **462**, NaN contract documented, survivorship-bias flag documented
- **`data-routing/SKILL.md`** — added `tickerall` / `nobitex` / `wallex` / `longbridge` / `mt5` / `pykrx` / `india_broker`; UK / KR / VN / Crypto IRR rows; explicit-source notes
- **`quant-research.md`** + **`data-priority.md`** — Tier-2 expanded; explicit-only and "never joins automatic fallback" notes added
- **`wealth-guide` agent** — Version 1.5 → **1.6** with v0.1.15 upgrade notes; `mcp__vibe-trading__*` wiring surfaced; skill count 180 → **184**
- **`alpha-researcher` / `backtest-builder` / `factor-researcher` / `market-router`** — markets covered + loader routing tables synced to v0.1.15 (Korea / Vietnam / UK engines, `BRK.B.US` class-share support, adjustment-caliber note)
- **`strategy-generate/SKILL.md`** — market detection table extended with UK / KR / VN / China Futures / Global Futures / explicit-only TickerAll; data-window-separated-from-evaluation window documented
- **`opencode.json`** — added `vibe-trading` MCP server (`vibe-trading-mcp`)
- **README** — Provenance row bumped to v0.1.15; Tier-3 sources expanded; Alpha Zoo 461 → **462**

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
- Vibe-Trading content (vendored as `vibe-trading-ai`, v0.1.15): MIT — see the upstream [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) repo
- Merged original code: Apache 2.0

---

**This repository is for research and analysis only. No live trading or order execution is permitted.**
