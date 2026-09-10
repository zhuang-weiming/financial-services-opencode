# Opencode for Financial Services (Wealth-Guide)

A unified financial-services AI agent platform powered by [Opencode](https://opencode.ai). Single-entry agent **Wealth-Guide** routes your question to the right specialized subagent — investment banking, equity research, private equity, wealth management, fund administration, and multi-market quantitative research.

## Provenance

| Source | License | Version | Contents |
|---|---|---|---|
| [Anthropic FSI](https://github.com/anthropic/claude-for-financial-services) | Apache 2.0 | — | 17 subagents, 59 institutional skills, 3 MCP connectors |
| [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | MIT | v0.1.15 | 90 skills, 462-alpha zoo (NaN contract), 10 backtest engines, 27 data loaders (UK / KRX / HOSE; explicit-only tickerall / nobitex / wallex), 30 swarm presets, 14 broker connectors, 74 MCP tools |
| [LLMQuant/skills](https://github.com/LLMQuant/skills) | MIT | v0.1.0 | 17 workflow routers (75 workflows) grounded in LLMQuant Data |
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | MIT | aihf 2.2.0 | 10 investor-persona skills (Buffett / Munger / Graham / Lynch / Druckenmiller + 4 mandates) |

## Quick Start

```bash
git clone <repo-url> financial-services-opencode && cd financial-services-opencode

# One-time setup
pip install -r .opencode/requirements.txt
pip install -e .opencode/python/vibe-trading      # vibe-trading-ai v0.1.15
pip install -e .opencode/python/wif-framework     # wif-framework v5.9.0
cd .opencode && npm install && cd ..              # optional — Opencode plugin only

opencode --agent wealth-guide
```

> Setup is one-time; the agent then runs with zero install delay. Both vendored
> packages install *editable*, and the data-loader extras (tushare / yfinance /
> akshare / pykrx / mootdx / baostock) are already resolved.

## Architecture

```
   wealth-guide  ← ONLY user-facing entry (intent → delegate)
        │ task(subagent=...)
        ├── IB / ER / PE / WM ── pitch-agent · earnings-reviewer · market-researcher · meeting-prep-agent
        ├── Modeling / Quant ── model-builder · alpha-researcher · backtest-builder · factor-researcher · market-router
        └── Fund-admin / KYC ── fund-admin · gl-reconciler · month-end-closer · statement-auditor · kyc-screener
             (+ swarm-orchestrator, financial-analysis, operations, valuation-reviewer, private-equity, …)
```

- **1 primary agent** + **22 subagents** (hidden) · **194 skills** — intent-routed, **100% coverage** ([governance](#skill-routing--coverage))
- **`vibe-trading-ai` v0.1.15** — vendored quant engine; namespace `src.*` / `backtest.*` / `cli.*`
- **MCP servers** — Morningstar · FactSet · llmquant-data · vibe-trading (optional)

## Subagent Reference

> **Every one of the 194 skills is listed below** — 238 assignments across 22 subagents, so a
> skill may appear under several. *(shared)* = protocol skills loaded by all subagents;
> *(tools)* = document/tooling skills available to all. Source of truth:
> [`skill-manifest.md`](.opencode/instructions/skill-manifest.md); intent routing:
> [`wealth-guide-router.md`](.opencode/instructions/wealth-guide-router.md).

| Subagent | Domain | skills |
|---|---|---|
| `investment-banking` | Investment Banking | `pitch-deck` · `cim-builder` · `teaser` · `deal-tracker` · `process-letter` · `merger-model` · `datapack-builder` · `buyer-list` · `strip-profile` |
| `equity-research` | Equity Research | `earnings-analysis` · `initiating-coverage` · `morning-note` · `catalyst-calendar` · `thesis-tracker` · `model-update` · `ai-hedge-fund` · `ai-hedge-fund-buffett` · `ai-hedge-fund-munger` · `ai-hedge-fund-graham` · `ai-hedge-fund-lynch` · `ai-hedge-fund-druckenmiller` · `ai-hedge-fund-deep-value` · `ai-hedge-fund-fundamental-ls` · `ai-hedge-fund-inflections` · `vibe-trading-deep-company-series` · `vibe-trading-dividend-analysis` · `vibe-trading-investor-lenses` · `vibe-trading-management-deep-dive` · `vibe-trading-report-generate` · `llmquant-equities` · `llmquant-investor-lenses` · `stock-deep-dive` |
| `private-equity` | Private Equity | `ic-memo` · `deal-screening` · `deal-sourcing` · `unit-economics` · `value-creation-plan` · `returns-analysis` · `dd-meeting-prep` · `vibe-trading-private-company-research` |
| `wealth-management` | Wealth Management | `client-report` · `client-review` · `financial-plan` · `investment-proposal` · `portfolio-rebalance` · `tax-loss-harvesting` · `wif-fund-advisory` · `wif-ashare-advisory` · `sell-ladder` · `vibe-trading-asset-allocation` · `vibe-trading-etf-analysis` · `vibe-trading-fund-analysis` · `vibe-trading-trade-journal` · `vibe-trading-shadow-account` · `llmquant-personal` · `llmquant-portfolio` · `llmquant-portfolio-lab` |
| `earnings-reviewer` | Equity Research (Earnings) | `earnings-analysis` · `earnings-preview` · `model-update` · `morning-note` · `ai-hedge-fund-earnings-drift` · `vibe-trading-earnings-forecast` · `vibe-trading-earnings-revision` · `llmquant-events` · `llmquant-news` |
| `meeting-prep-agent` | Wealth Management (Meeting Prep) | `client-review` · `client-report` · `investment-proposal` |
| `pitch-agent` | Investment Banking (Pitch) | `pitch-deck` · `comps-analysis` · `dcf-model` · `ib-check-deck` · `deck-refresh` · `lbo-model` |
| `market-researcher` | Equity Research (Sector) | `sector-overview` · `competitive-analysis` · `comps-analysis` · `idea-generation` · `vibe-trading-ashare-pre-st-filter` · `vibe-trading-bottleneck-hunter` · `vibe-trading-commodity-analysis` · `vibe-trading-convertible-bond` · `vibe-trading-edgar-sec-filings` · `vibe-trading-fundamental-filter` · `vibe-trading-geopolitical-risk` · `vibe-trading-regulatory-knowledge` · `vibe-trading-sector-rotation` · `vibe-trading-sentiment-analysis` · `vibe-trading-social-media-intelligence` · `vibe-trading-us-etf-flow` · `llmquant-commodities` · `llmquant-etfs` · `llmquant-funds` · `llmquant-market-intelligence` · `llmquant-polymarket` · `llmquant-prediction-markets` · `llmquant-sec` |
| `model-builder` | Financial Modeling | `dcf-model` · `lbo-model` · `3-statement-model` · `comps-analysis` · `vibe-trading-valuation-model` |
| `financial-analysis` | Cross-Domain Financial Analysis | `3-statement-model` · `dcf-model` · `lbo-model` · `comps-analysis` · `competitive-analysis` · `ai-hedge-fund-graham` · `ai-hedge-fund-deep-value` · `vibe-trading-credit-analysis` · `vibe-trading-financial-statement` · `vibe-trading-valuation-model` · `llmquant-credit` · `llmquant-equity-derivatives` |
| `alpha-researcher` | Quantitative Research (Alpha) | `vibe-trading-alpha-zoo` · `vibe-trading-factor-research` · `vibe-trading-multi-factor` · `vibe-trading-quant-statistics` · `alpha-engine-v21` · `trend-analysis-multi-algo` · `non-price-evidence` · `vibe-trading-candlestick` · `vibe-trading-chanlun` · `vibe-trading-elliott-wave` · `vibe-trading-gann` · `vibe-trading-harmonic` · `vibe-trading-ichimoku` · `vibe-trading-smc` · `vibe-trading-technical-basic` · `llmquant-research` |
| `factor-researcher` | Quantitative Research (Factors) | `vibe-trading-factor-research` · `vibe-trading-multi-factor` · `vibe-trading-correlation-analysis` · `vibe-trading-correlation-regime` · `alpha-engine-v21` · `ai-hedge-fund-druckenmiller` · `ai-hedge-fund-earnings-drift` · `ai-hedge-fund-inflections` · `vibe-trading-behavioral-finance` · `vibe-trading-market-microstructure` · `vibe-trading-options-advanced` · `vibe-trading-options-payoff` · `vibe-trading-options-strategy` · `vibe-trading-performance-attribution` · `vibe-trading-quant-statistics` · `vibe-trading-volatility` · `llmquant-options` |
| `backtest-builder` | Quantitative Research (Backtest) | `vibe-trading-strategy-generate` · `vibe-trading-backtest-diagnose` · `vibe-trading-strategy-dev-manager` · `alpha-engine-v21` · `vibe-trading-corporate-events` · `vibe-trading-cross-market-strategy` · `vibe-trading-event-driven` · `vibe-trading-execution-model` · `vibe-trading-minute-analysis` · `vibe-trading-ml-strategy` · `vibe-trading-pair-trading` · `vibe-trading-pine-script` · `vibe-trading-seasonal` · `vibe-trading-strategy-discovery` · `vibe-trading-vnpy-export` · `llmquant-strategies` |
| `market-router` | Cross-Market Data Routing | `vibe-trading-data-routing` · `vibe-trading-tushare` · `vibe-trading-yfinance` · `vibe-trading-akshare` · `vibe-trading-mootdx` · `vibe-trading-okx-market` · `vibe-trading-ccxt` · `llmquant-rates-fx` · `vibe-trading-correlation-regime` · `vibe-trading-adr-hshare` · `vibe-trading-crypto-derivatives` · `vibe-trading-defi-yield` · `vibe-trading-eastmoney` · `vibe-trading-global-macro` · `vibe-trading-hk-connect-flow` · `vibe-trading-liquidation-heatmap` · `vibe-trading-macro-analysis` · `vibe-trading-onchain-analysis` · `vibe-trading-perp-funding-basis` · `vibe-trading-qveris` · `vibe-trading-sec-edgar` · `vibe-trading-stablecoin-flow` · `vibe-trading-token-unlock-treasury` · `llmquant-crypto` · `llmquant-data` · `llmquant-macro` · `llmquant-market-data` |
| `swarm-orchestrator` | Multi-Agent Orchestration | `ai-hedge-fund` · `ai-hedge-fund-buffett` · `ai-hedge-fund-munger` · `ai-hedge-fund-graham` · `ai-hedge-fund-lynch` · `ai-hedge-fund-druckenmiller` · `ai-hedge-fund-fundamental-ls` |
| `fund-admin` | Fund Administration | `nav-tieout` · `accrual-schedule` · `roll-forward` · `variance-commentary` |
| `gl-reconciler` | Fund General Ledger | `gl-recon` · `break-trace` |
| `month-end-closer` | Fund Month-End Close | `accrual-schedule` · `roll-forward` · `variance-commentary` |
| `statement-auditor` | LP Statement Audit | `nav-tieout` · `audit-xls` |
| `valuation-reviewer` | Valuation Review | `returns-analysis` · `portfolio-monitoring` · `ic-memo` · `vibe-trading-hedging-strategy` · `vibe-trading-risk-analysis` · `llmquant-risk` |
| `kyc-screener` | KYC / AML Compliance | `kyc-doc-parse` · `kyc-rules` |
| `operations` | Private Equity Operations | `portfolio-monitoring` · `ai-readiness` · `dd-checklist` · `deal-sourcing` · `value-creation-plan` |
| *(shared)* | All subagents | `5-why-adversary` · `personal-trading-system` · `buy-ladder` · `vibe-trading-research-discipline` · `vibe-trading-research-goal` |
| *(tools)* | All subagents (tooling) | `docx` · `pdf` · `xlsx` · `xlsx-author` · `pptx` · `pptx-author` · `clean-data-xls` · `ppt-template-creator` · `skill-creator` · `vibe-trading-doc-reader` · `vibe-trading-web-reader` |

> **Router drift found.** Three names in the router's registry are **not real skills** and
> were corrected above: `factor-analysis` → `vibe-trading-multi-factor`; `crypto-market-analysis`
> → `vibe-trading-okx-market` / `vibe-trading-ccxt`; `fx-market-analysis` → `llmquant-rates-fx`.
> The router also lists `IC/IR` and `quantile backtest` as if they were skills — they are
> capabilities of `vibe-trading-factor-research`.

## Three-Layer Analysis Stack

**Price-layer consensus is *pseudo-independent*** (all algorithms read one OHLCV series) — the non-price and fundamental layers are what make a verdict robust. Agreement raises confidence; **disagreement localizes the decision's assumption**.

| Layer | Skill | Answers | Run |
|---|---|---|---|
| **Price** | `trend-analysis-multi-algo` | direction / support-resistance / patterns | `trend_analysis.py --code X --market sh` |
| **Evidence** | `non-price-evidence` | volume / fund-flow / fundamentals / macro | `fetch_evidence.py --code X --market sh` |
| **Fundamental** | `ai-hedge-fund-*` | business quality / valuation / inflection | `build_snapshot.py --code X --market sh --render` |

*(all three scripts live under `.opencode/skills/<skill>/scripts/`)*

**`trend-analysis-multi-algo` — 10 algorithms.** One command runs all ten; **never conclude from a single algorithm** (WaveTrend-only is a documented failure mode). Momentum: WaveTrend (V21: N1=50/N2=105) + technical 3-way vote. Pattern: candlestick (15) · 缠论 · Elliott · harmonic. Structure: SMC/ICT · Ichimoku · Gann. Output includes an **independence caveat** (10/10 are transforms of one series).

**`non-price-evidence` — 4 dimensions.** Volume structure (turnover / volume-ratio / OBV / AD-line) · fund flow (margin / holder-count / dragon-tiger / block-trade / lockup / northbound) · fundamentals (东财 indicators + consensus) · macro (China CPI/PPI/M2/社融/GDP). MCP extends each (minute/tick/Level-2, US 13F/Form 4, SEC text, FRED, Polymarket). Every run reports per-source status, coverage **gaps**, and **stale flags** — a conclusion can never silently rest on missing data.

**`ai-hedge-fund-*` — 10 investor-persona skills.** Ported from [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) with **exact upstream system prompts** + a local data adapter (no `aihf` install or API key). Master `ai-hedge-fund` (FUND > STRATEGY > MODEL) · personas `{buffett,munger,graham,lynch,druckenmiller}` · mandates `{deep-value,earnings-drift,fundamental-ls,inflections}`. **Aggregate trigger** 「投资大佬」/「各位大佬」/「投资大师」 loads all five and returns a consensus/divergence table.

> **Snapshot fidelity.** Output validates against upstream's Pydantic models with **zero extra fields** (14 period fields + 6 aggregates, upstream's exact formulas). **No invented metrics** — no `PEG`, no `earnings_growth` (not in the schema).
> **Known gaps:** `current_ratio` unavailable for financial firms; `free_cash_flow_per_share` uses 东财 每股经营现金流 (operating cash flow, not net of capex).

### Trigger phrases

| You say | Layer(s) |
|---|---|
| 趋势分析 / 技术分析 / 缠论 / 波浪 / 蜡烛图 / 支撑压力 | Price only |
| 资金流向 / 龙虎榜 / 两融 / 北向 / 非价格证据 | Evidence only |
| 投资大佬 / 各位大佬 / 巴菲特视角 / 林奇 PEG | Fundamental only |
| **综合分析 / 全栈分析 / 三层分析 / 投资大佬 + 趋势** | **All three** |

## Skill Routing & Coverage

Routing is **intent-driven** — the user never needs to know a skill name.

```
Layer 1  intent → subagent   wealth-guide-router.md   (hand-written, ~20 subagents)
Layer 2  skill discovery     skill-manifest.md        (auto-generated, 194 skills)
Layer 3  coverage gate       tests/test_skills.py::test_skill_routing_coverage
```

```bash
python3 .opencode/scripts/gen_skill_manifest.py           # regenerate the manifest
python3 .opencode/scripts/gen_skill_manifest.py --check   # CI: non-zero exit on any unregistered routable skill
```

- Coverage is asserted at **194/194**; tool/meta skills (`docx`/`pdf`/…) are exempt and `_shared` is an internal resource dir.
- **Adding a skill?** Create it → run `gen_skill_manifest.py` → run `--check`.
- ⚠️ **Frontmatter is YAML.** A `: ` (colon + space) inside an unquoted `description` breaks parsing and the skill will not load.

## Data Sources

### Tier 1 — Institutional MCP (preferred)
- **Morningstar** — analyst research, fund data, fair value, screeners, ownership
- **FactSet** — financial statements, valuation, market intelligence
- **llmquant-data** — US equity/crypto OHLCV, ETF holdings (SEC N-PORT), FRED macro, AI-summarized news, SEC 13F, 10-K/Q/8-K text, Polymarket odds, papers/wiki (25 tools)

### Tier 2 — General web
- **DuckDuckGo Search** — supplementary only

### Tier 3 — Quantitative loaders (`vibe-trading-ai` v0.1.15)

| Market | Sources |
|---|---|
| A-Share | MooTDX, Tencent, Sina, Baostock, AKShare, EastMoney, Tushare |
| US / Global | Yahoo, Stooq, EastMoney, Finnhub, Alpha Vantage, Tiingo, FMP |
| HK | Tencent, EastMoney, Yahoo, LongBridge, Futu |
| Canada / India | Yahoo (`.TO`/`.V` · `.NS`/`.BO`); India broker loaders read-only |
| Korea (KRX) | pykrx (Naver-adjusted); Yahoo fallback |
| Vietnam (HOSE) | Yahoo (`.VN`); long-only, ±7% band |
| UK (LSE) | Yahoo (`.L`/`.IL`); SDRT 0.5% purchase-side |
| Crypto | OKX, CCXT; nobitex / wallex (Toman) explicit-only |
| Futures / FX / Metals | AKShare (China), Yahoo, MT5 (local), TickerAll (hosted, explicit-only) |
| SEC filings | EDGAR client (`backtest.loaders.sec_edgar_client`) |

> **Data-quality rules** (`.opencode/instructions/data-priority.md`): prefer MCP over free
> loaders; mark unsourced figures `[UNSOURCED]`. v0.1.15 adds: every price frame carries an
> **adjustment caliber** (cite it); **NaN propagates** through the alpha zoo (quote IC with the
> post-drop sample size); **`pct_change()` does not forward-fill**.

## Alpha Zoo (462 factors)

`qlib158` 158 (Qlib; `equity_cn`/`equity_in`/`equity_kr`) · `alpha101` 101 (Kakushadze) · `gtja191` 191 (China) · `academic` (Fama-French / Carhart) · `fundamental`.

```python
from src.factors.registry import Registry
zoo = Registry.get_alpha("qlib158")
```

## LLMQuant Workflow Skills

17 routers / 75 workflows from [LLMQuant/skills](https://github.com/LLMQuant/skills), grounded in `llmquant-data`. Full mapping: `.opencode/instructions/llmquant-skills.md`.

`options` (10) · `investor-lenses` (17) · `strategies` (6) · `equities` (5) · `portfolio` (5) · `risk` (4) · `credit` (3) · `crypto` (3) · `events` (3) · `macro` (3) · `market-intelligence` (3) · `prediction-markets` (3) · `rates-fx` (3) · `commodities` (2) · `equity-derivatives` (2) · `portfolio-lab` (2) · `etfs` (1) — routed to `factor-researcher` / `equity-research` / `backtest-builder` / `wealth-management` / `market-router` / `market-researcher` / `financial-analysis` / `valuation-reviewer` / `earnings-reviewer`.

## MCP Configuration

Config: `.opencode/mcp/servers.json`. Bring your own keys:

```bash
export MORNINGSTAR_API_KEY="your-key"
export FACTSET_API_KEY="your-key"
export LLMQUANT_API_KEY="your-key"
```

Without MCP keys the system falls back to Tier 2 (DDG) and Tier 3 (free loaders).

## Cookbooks (`./example/`)

Each subagent has a cookbook (sample data + question sets) — tutorials and test cases.

```bash
opencode --agent wealth-guide --prompt "$(cat example/earnings-reviewer/questions.md)"
```

## Testing

```bash
python tests/run_all.py                              # full suite
python3 .opencode/scripts/gen_skill_manifest.py --check   # routing-coverage gate
```

Covers: structural (agent/skill frontmatter), integration (alpha Registry, live-trade
detection, MCP integrity), business acceptance (Chinese queries, cross-domain routing,
adversarial cross-contamination), unit (routing, pipeline), and **skill routing coverage**
(`test_skill_routing_coverage` asserts 0 routable-but-unregistered; `test_skill_manifest_fresh`
asserts the manifest matches disk).

**Baseline:** 1424 tests · 1394 passed · 2 pre-existing failures (memory-file naming, BT directory structure — both unrelated).

## Changelog

| Version | Date | Headline |
|---|---|---|
| **v1.8** | 2026-09-10 | **Analysis stack + routing governance.** `trend-analysis-multi-algo` (10 algorithms), `non-price-evidence` (4 dimensions), `ai-hedge-fund-*` (10 persona skills, upstream-faithful snapshot). Skill count 183 → **194**. Added `gen_skill_manifest.py` + `skill-manifest.md` + coverage test. Fixed broken `vibe-trading-gann`. |
| v1.7 | 2026-09-10 | Renamed 89 Vibe-Trading skills → `vibe-trading-*`; removed redundant `vibe-thesis-tracker`; clarified the two skill systems (OpenCode vs vendored package). |
| v1.6.1 | 2026-09-10 | Re-merge audit: `.opencode/python/vibe-trading/` v0.1.13 → **v0.1.15**; restored 12 missing v0.1.15 modules; content-synced 37 skills. |
| v1.6 | 2026-09-10 | Vibe-Trading v0.1.15 sync — 462 alphas (NaN contract), `pct_change()` no forward-fill, adjustment caliber, UK/KRX/HOSE, explicit-only sources. |
| v1.5 | 2026-08-29 | LLMQuant integration — 17 workflow routers (75 workflows) + `llmquant-data` MCP (25 tools). |
| v1.0 | — | Initial release: Anthropic FSI + Vibe-Trading + 22 subagents. |

## License

- Anthropic FSI content: Apache 2.0
- Vibe-Trading content (`vibe-trading-ai` v0.1.15): MIT — [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading)
- LLMQuant/skills content: MIT
- Merged original code: Apache 2.0

---

**This repository is for research and analysis only. No live trading or order execution is permitted.**
