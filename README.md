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

- **1 primary agent** + **22 subagents** (hidden) · **195 skills** — intent-routed, **100% coverage** ([governance](#skill-routing--coverage))
- **`vibe-trading-ai` v0.1.15** — vendored quant engine; namespace `src.*` / `backtest.*` / `cli.*`
- **MCP servers** — Morningstar · FactSet · llmquant-data · vibe-trading (optional)

## Subagent Reference

> **Capabilities, not skill names.** *Key* = how many skills
> [`wealth-guide-router.md`](.opencode/instructions/wealth-guide-router.md) names for that
> subagent — a curated subset, **not a limit** (skills can appear under several subagents;
> 62 unique skills named in total). Full list: [`skill-manifest.md`](.opencode/instructions/skill-manifest.md).

| Subagent | Domain | Key | Capabilities |
|---|---|:---:|---|
| `investment-banking` | IB | 8 | Pitch decks, CIMs, teasers, buyer lists, merger models, deal tracking |
| `equity-research` | ER | 6 | Earnings analysis, initiating coverage, morning notes, thesis tracking, **investor personas** |
| `private-equity` | PE | 6 | IC memos, deal screening/sourcing, unit economics, returns analysis |
| `wealth-management` | WM | 7 | Financial plans, rebalancing, TLH, client reports, WIF advisory |
| `earnings-reviewer` | ER | 4 | Post-earnings: transcript → model → note |
| `meeting-prep-agent` | WM | 3 | Client/investor meeting prep packs |
| `pitch-agent` | IB | 6 | Buy-side pitch decks, comps, DCF, LBO, football field |
| `market-researcher` | ER | 4 | Sector primers, competitive landscapes, idea generation |
| `model-builder` | Modeling | 3 | DCF, LBO, 3-statement, comps from scratch |
| `financial-analysis` | Cross-domain | 4 | 3-statement, DCF, LBO, comps, competitive analysis |
| `alpha-researcher` | Quant | 4 | Alpha zoo, IC/IR, factor bench, strategy research |
| `factor-researcher` | Quant | 3 | IC/IR, quantile backtest, correlation, risk decomposition |
| `backtest-builder` | Quant | 4 | Strategy generation, backtesting, walk-forward, diagnosis |
| `market-router` | Cross-market | 6 | Data routing (A-share / US / HK / crypto / FX / futures / India / Korea / Vietnam / UK / Canada) |
| `swarm-orchestrator` | Multi-agent | — | 30 preset research teams |
| `fund-admin` | Fund admin | 4 | NAV tie-out, accruals, roll-forwards, variance commentary |
| `gl-reconciler` | Fund GL | 2 | GL reconciliation, break classification, root-cause trace |
| `month-end-closer` | Month-end | 3 | Accrual schedules, roll-forwards, close packages |
| `statement-auditor` | LP audit | 2 | NAV tie-out, formula audit, cross-statement consistency |
| `valuation-reviewer` | Valuation QA | 3 | Assumption stress-test, sensitivity analysis, model challenge |
| `kyc-screener` | KYC/AML | 2 | Onboarding parse, AML rules engine, risk rating |
| `operations` | PE ops | 5 | Portfolio monitoring, AI readiness, DD checklists, value creation |

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
Layer 2  skill discovery     skill-manifest.md        (auto-generated, 195 skills)
Layer 3  coverage gate       tests/test_skills.py::test_skill_routing_coverage
```

```bash
python3 .opencode/scripts/gen_skill_manifest.py           # regenerate the manifest
python3 .opencode/scripts/gen_skill_manifest.py --check   # CI: non-zero exit on any unregistered routable skill
```

- Coverage is asserted at **195/195**; tool/meta skills (`docx`/`pdf`/…) are exempt and `_shared` is an internal resource dir.
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
| **v1.8** | 2026-09-10 | **Analysis stack + routing governance.** `trend-analysis-multi-algo` (10 algorithms), `non-price-evidence` (4 dimensions), `ai-hedge-fund-*` (10 persona skills, upstream-faithful snapshot). Skill count 183 → **195**. Added `gen_skill_manifest.py` + `skill-manifest.md` + coverage test. Fixed broken `vibe-trading-gann`. |
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
