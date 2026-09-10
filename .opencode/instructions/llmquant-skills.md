# LLMQuant Skills Registry — Category, Scenarios, Triggers, Subagent Mapping

> **Imported from** [`github.com/LLMQuant/skills`](https://github.com/LLMQuant/skills) (MIT, v0.1.0) on 2026-08-29.
> **Scope**: 17 category router skills + 75 workflow files, grounded in the `llmquant-data` MCP (25 tools).
> **Excluded**: `llmquant-data` (naming collision with the project's existing master+subskills tool-reference layer — see §Layering).

---

## Layering (how the three llmquant layers fit together)

```
Layer 1  MCP tools (25)           llmquant-data_*  raw data access (crypto/equity/ETF/macro/news/13F/filings/polymarket/personal)
Layer 2  Tool-reference skills (9)  llmquant-data (master) + 8 domain subskills  HOW to call each tool
Layer 3  Workflow-router skills (17) llmquant-* categories  WHAT analysis to run (this registry)
```

- **Layer 2** (`llmquant-market-data`, `llmquant-funds`, `llmquant-macro`, `llmquant-news`, `llmquant-research`, `llmquant-polymarket`, `llmquant-sec`, `llmquant-personal`) documents *tool-by-tool* usage (params, returns, cost, coverage flags).
- **Layer 3** (the 17 skills below) documents *workflow-by-workflow* procedures that orchestrate those tools into a deliverable.
- A subagent should load the **Layer 2** skill when the user asks *"get me X data"* and the **Layer 3** skill when the user asks *"run analysis Y / produce deliverable Z"*.

---

## Category Taxonomy (17 skills)

| # | Skill | Category | Workflows | Primary subagent(s) |
|---|---|---:|---|---|
| 1 | `llmquant-commodities` | commodities | 2 | `market-researcher` / `market-router` |
| 2 | `llmquant-credit` | credit | 3 | `financial-analysis` / `market-researcher` |
| 3 | `llmquant-crypto` | crypto | 3 | `market-router` / `factor-researcher` |
| 4 | `llmquant-equities` | equities | 5 | `equity-research` / `earnings-reviewer` |
| 5 | `llmquant-equity-derivatives` | equity-derivatives | 2 | `financial-analysis` / `factor-researcher` |
| 6 | `llmquant-etfs` | etfs | 1 | `market-researcher` / `financial-analysis` |
| 7 | `llmquant-events` | events | 3 | `earnings-reviewer` / `market-researcher` |
| 8 | `llmquant-investor-lenses` | investor-lenses | 17 | `equity-research` / `wealth-management` |
| 9 | `llmquant-macro` | macro | 3 | `market-router` / `factor-researcher` / `wealth-management` |
| 10 | `llmquant-market-intelligence` | market-intelligence | 3 | `market-researcher` / `equity-research` |
| 11 | `llmquant-options` | options | 10 | `factor-researcher` / `financial-analysis` |
| 12 | `llmquant-portfolio` | portfolio | 5 | `wealth-management` / `equity-research` |
| 13 | `llmquant-portfolio-lab` | portfolio-lab | 2 | `wealth-management` / `valuation-reviewer` |
| 14 | `llmquant-prediction-markets` | prediction-markets | 3 | `market-researcher` / `market-router` |
| 15 | `llmquant-rates-fx` | rates-fx | 3 | `market-router` / `factor-researcher` |
| 16 | `llmquant-risk` | risk | 4 | `valuation-reviewer` / `factor-researcher` |
| 17 | `llmquant-strategies` | strategies | 6 | `backtest-builder` / `swarm-orchestrator` |

**Total**: 17 routers, 75 workflows. 16 shipped as-is; `llmquant-macro` merged into the existing tool-reference macro skill (3 workflows added); `llmquant-strategies` and `llmquant-investor-lenses` shipped with integration notes (voice/tone + persona-grounding).

---

## Per-Skill Scenario Detail

### 1. `llmquant-commodities` — Commodities
- **Purpose**: commodity spot, futures curve, inventory, roll yield, macro linkage.
- **Workflows**: `commodity-market-lens` (price/curve/inventory/macro brief), `futures-curve-monitor` (term structure, contango/backwardation, roll yield).
- **Scenarios**: "oil supply-demand balance", "is WTI in backwardation", "gold vs real rates", "copper as growth proxy", "futures roll yield".
- **Triggers**: commodity, WTI, Brent, gold, copper, crude, futures curve, contango, backwardation, roll yield, inventory.
- **Combine with (legacy)**: `vibe-trading-commodity-analysis` (signal generation), `vibe-trading-global-macro` (macro linkage).
- **Data note**: commodity-specific endpoints are partially future product surface — workflows name the missing input and continue with macro/equity proxies.

### 2. `llmquant-credit` — Credit
- **Purpose**: issuer credit risk, spread regime, high-yield stress, default/refinancing risk.
- **Workflows**: `issuer-credit-risk-review`, `credit-spread-regime`, `high-yield-stress-monitor`.
- **Scenarios**: "can X refinance its debt", "is HY spread signaling stress", "fallen angel watchlist", "covenant headroom", "issuer default risk".
- **Triggers**: credit, CDS, spread, high-yield, HY, fallen angel, default, refinancing, covenant, maturity wall, bond.
- **Combine with (legacy)**: `vibe-trading-credit-analysis` (rating/spread methodology), `vibe-trading-financial-statement` (debt schedule forensics), `vibe-trading-global-macro` (spread regime).
- **Data note**: bond/CDS/rating endpoints may be unavailable — fall back to filings + equity + rates evidence, naming the gap.

### 3. `llmquant-crypto` — Crypto
- **Purpose**: crypto market regime, token research, perpetual funding/basis/leverage monitoring.
- **Workflows**: `crypto-market-regime`, `crypto-token-research`, `crypto-perp-funding-monitor`.
- **Scenarios**: "BTC regime analysis", "token due diligence", "funding-rate crowdedness", "basis trade", "open-interest leverage".
- **Triggers**: BTC, ETH, crypto, token, perp funding, basis, open interest, liquidation, TVL, on-chain, altcoin.
- **Combine with (legacy)**: `vibe-trading-perp-funding-basis` (funding/carry mechanics), `vibe-trading-onchain-analysis` (MVRV/NVT/SOPR), `vibe-trading-stablecoin-flow`, `vibe-trading-liquidation-heatmap`.
- **Data note**: `llmquant-market-data` (Layer 2) provides spot/OHLCV; funding/open-interest/tokenomics may be future endpoints.

### 4. `llmquant-equities` — Equities
- **Purpose**: equity research, comparison, valuation, catalysts, sell discipline.
- **Workflows**: `five-lens-stock-analysis` (fundamentals/valuation/technicals/sentiment/flow scoring), `equity-compare`, `equity-research-memo`, `merger-arb-memo`, `take-profit-lab`.
- **Scenarios**: "analyze AAPL", "compare NVDA vs AMD", "write a research memo", "merger arb spread", "when to take profit".
- **Triggers**: stock analysis, equity research, compare stocks, valuation, catalyst, merger arb, take profit, sell discipline, five-lens.
- **Combine with (legacy)**: `stock-deep-dive` (multi-skill综合), `thesis-tracker` (buy-side discipline), `initiating-coverage`, `idea-generation`.
- **Data note**: the five-lens workflow has a 0-10 scoring rubric and target/stop framework; it is the highest-signal single-stock workflow.

### 5. `llmquant-equity-derivatives` — Equity Derivatives
- **Purpose**: single-stock derivative and hybrid-security research (payoff, Greeks, dilution, borrow, catalysts).
- **Workflows**: `single-stock-derivative-playbook`, `convertible-and-warrant-lens`.
- **Scenarios**: "single-stock option playbook", "convertible bond analysis", "warrant valuation", "dilution impact", "hybrid security".
- **Triggers**: convertible, warrant, rights, dilution, single-stock derivative, hybrid security, payoff, anti-dilution.
- **Combine with (legacy)**: `vibe-trading-convertible-bond` (转股/纯债/期权三维), `vibe-trading-options-strategy` (Greeks), `vibe-trading-corporate-events` (dilution events).

### 6. `llmquant-etfs` — ETFs
- **Purpose**: ETF holdings, overlap, concentration, exposure analysis.
- **Workflows**: `etf-overlap-report` (shared holdings, weight, concentration, N-PORT staleness).
- **Scenarios**: "SPY vs VTI overlap", "QQQ concentration", "ETF sector exposure", "IBIT holdings".
- **Triggers**: ETF, holdings, overlap, concentration, top constituents, N-PORT, fund exposure.
- **Combine with (legacy)**: `vibe-trading-etf-analysis` (fund selection/fees/tracking error), `vibe-trading-us-etf-flow` (creation/redemption flows), `llmquant-funds` (Layer 2 holdings lookup).
- **Data note**: always match holdings by CUSIP/ISIN, not ticker (nullable for bonds/cash/non-US); N-PORT is quarterly — cite `as_of_date`.

### 7. `llmquant-events` — Events
- **Purpose**: earnings, M&A, regulatory/legal/policy catalysts and event-risk monitoring.
- **Workflows**: `earnings-event-brief`, `mna-event-tracker`, `regulatory-risk-monitor`.
- **Scenarios**: "pre-earnings setup", "M&A deal spread + break risk", "FDA/antitrust regulatory risk", "event calendar".
- **Triggers**: earnings event, M&A, deal spread, break risk, regulatory, antitrust, FDA, legal, policy, catalyst calendar.
- **Combine with (legacy)**: `earnings-preview` / `earnings-analysis`, `vibe-trading-corporate-events` (event-driven), `catalyst-calendar`, `vibe-trading-event-driven` (backtest).

### 8. `llmquant-investor-lenses` — Investor Lenses (persona overlays)
- **Purpose**: investor-style reasoning overlays grounded in LLMQuant Data evidence.
- **Workflows** (17): `warren-buffett`, `ben-graham`, `charlie-munger`, `mohnish-pabrai`, `rakesh-jhunjhunwala`, `peter-lynch`, `phil-fisher`, `cathie-wood`, `stanley-druckenmiller`, `bill-ackman`, `michael-burry`, `nassim-taleb`, `aswath-damodaran`, `warren-buffett-scorecard`, `duan-yongping-seller`, `howard-marks-cycle`, `david-tepper-panic-signal`.
- **Scenarios**: "how would Buffett evaluate X", "Graham margin of safety", "Lynch ten-bagger screen", "Burry filing-first downside", "Taleb tail-risk barbell", "Tepper panic-buy gate".
- **Triggers**: Buffett, Graham, Munger, Lynch, Fisher, Cathie Wood, Druckenmiller, Ackman, Burry, Taleb, Damodaran, 段永平, Howard Marks, Tepper, margin of safety, moat, circle of competence.
- **Combine with (legacy)**: `vibe-trading-behavioral-finance` (bias checklist), `vibe-trading-management-deep-dive` (段永平 3-question verdict).
- **⚠️ Persona grounding**: each lens is an *analytical frame*, not the investor's actual view. Never fabricate biographical quotes, personal holdings, or positions. Evidence must come from LLMQuant Data.

### 9. `llmquant-macro` — Macro
- **Purpose**: macro dashboards, central-bank previews, liquidity/growth/inflation, portfolio impact.
- **Workflows**: `global-macro-dashboard`, `fed-policy-preview`, `macro-to-portfolio-impact`.
- **Scenarios**: "global macro snapshot", "pre-FOMC preview", "how does this macro regime hit my portfolio".
- **Triggers**: macro, Fed, FOMC, CPI, PMI, liquidity, growth, inflation, central bank, macro dashboard.
- **Combine with (legacy)**: `vibe-trading-macro-analysis` (cycle positioning), `vibe-trading-global-macro` (CB policy transmission), `wif-fund-advisory` / `wif-ashare-advisory` (WIF phase timing).
- **Layer 2 note**: the tool reference (how to call `macro_indicator_*`) is in this same skill's body; the 3 workflows are in `workflows/`.

### 10. `llmquant-market-intelligence` — Market Intelligence
- **Purpose**: reusable market utility/signal views.
- **Workflows**: `macro-view`, `market-sentiment`, `event-probability-signals`.
- **Scenarios**: "market sentiment dashboard", "macro view", "compare prediction-market vs options-implied odds".
- **Triggers**: market sentiment, breadth, put/call, macro view, event probability, cross-asset.
- **Combine with (legacy)**: `vibe-trading-sentiment-analysis` (恐贪/PCR/融资融券), `morning-note` (overnight brief), `vibe-trading-us-etf-flow` (breadth).

### 11. `llmquant-options` — Options
- **Purpose**: options, volatility, Greeks, unusual activity, option backtests.
- **Workflows** (10): `iv-rank`, `options-score`, `vibe-trading-options-strategy`, `greeks-dashboard`, `pnl-simulator`, `volatility-surface`, `volatility-smile`, `unusual-activity`, `earnings-iv-crush`, `bull-put-spread-backtest`.
- **Scenarios**: "is IV cheap or expensive", "build a covered-call/put-spread", "Greeks dashboard", "P&L at expiry", "vol smile/skew", "unusual option activity", "earnings IV crush", "option strategy backtest".
- **Triggers**: IV, implied volatility, IV rank, Greeks, delta, theta, options strategy, volatility surface, skew, put spread, covered call, unusual activity, IV crush.
- **Combine with (legacy)**: `vibe-trading-options-strategy` (BS/Greeks/backtest), `vibe-trading-options-payoff` (payoff diagrams), `vibe-trading-options-advanced` (vol surface SABR/Local Vol), `vibe-trading-volatility` (HV percentile mean-reversion).

### 12. `llmquant-portfolio` — Portfolio Workspace
- **Purpose**: persistent research workspace — company profiles, thesis tracking, themes, watchlists, alerts.
- **Workflows**: `company-profile`, `investment-thesis-tracker`, `theme-research`, `watchlist-monitor`, `alert-manager`.
- **Scenarios**: "build a company profile", "write/inspect a buy thesis with sell conditions", "track a theme basket", "monitor a watchlist", "set price/IV/event alerts".
- **Triggers**: company profile, thesis, watchlist, alert, theme basket, monitor.
- **Combine with (legacy)**: `thesis-tracker` (quarterly re-check), `portfolio-monitoring` (variance to plan), `client-report`.

### 13. `llmquant-portfolio-lab` — Portfolio Lab
- **Purpose**: portfolio exposure maps, what-if simulations, virtual portfolio states.
- **Workflows**: `portfolio-exposure-map` (holdings/sectors/factors/geography/ETF look-through/concentration), `portfolio-what-if-simulator` (adds/trims/hedges/shocks).
- **Scenarios**: "what's my sector/factor exposure", "what if I add X / trim Y / hedge Z", "stress a hypothetical portfolio".
- **Triggers**: exposure map, what-if, scenario, pro-forma portfolio, factor exposure, concentration, hedge simulation.
- **Combine with (legacy)**: `portfolio-rebalance` (drift trades), `vibe-trading-risk-analysis` (VaR/CVaR/stress), `vibe-trading-asset-allocation`.

### 14. `llmquant-prediction-markets` — Prediction Markets
- **Purpose**: event odds, settlement criteria, probability gaps, cross-market/venue arb.
- **Workflows**: `event-probability-brief`, `prediction-market-arb-watch`, `probability-vs-options-pricing`.
- **Scenarios**: "Fed cut probability", "event odds brief", "arb between venues/contracts", "polymarket vs options-implied odds".
- **Triggers**: prediction market, Polymarket, event odds, implied probability, Fed cut odds, M&A odds, arb.
- **Combine with (legacy)**: none direct (new domain). Layer 2 `llmquant-polymarket` provides the price-history/settlement tools.

### 15. `llmquant-rates-fx` — Rates & FX
- **Purpose**: yield curve, duration, central-bank divergence, FX carry, currency risk.
- **Workflows**: `yield-curve-trade-lens`, `central-bank-divergence`, `fx-carry-dashboard`.
- **Scenarios**: "curve steepener/flattener", "duration positioning", "Fed vs ECB divergence", "FX carry screen", "dollar/TWUSD".
- **Triggers**: yield curve, duration, steepener, flattener, central bank, ECB/BoJ/BOE, FX carry, USD, EUR, JPY, real rate.
- **Combine with (legacy)**: `vibe-trading-global-macro` (CB policy), `vibe-trading-macro-analysis`, `llmquant-macro` (Layer 2 FRED indicators).

### 16. `llmquant-risk` — Risk
- **Purpose**: risk regime, hedging, panic scoring, research-quality checks.
- **Workflows**: `fear-score` (per-ticker panic), `vix-status` (options-risk regime), `hedge-advisor` (puts/collars/put-spreads), `research-health-check` (stale profiles/thesis drift audit).
- **Scenarios**: "panic score for X", "VIX regime", "design a hedge", "audit my research for staleness".
- **Triggers**: fear score, panic, VIX, hedge, collar, protective put, risk regime, research health, thesis drift.
- **Combine with (legacy)**: `vibe-trading-risk-analysis` (VaR/CVaR/Monte Carlo), `vibe-trading-correlation-regime` (fusion/defused state), `vibe-trading-hedging-strategy`, `5-why-adversary` (adversarial QC).

### 17. `llmquant-strategies` — Strategies (PM playbooks)
- **Purpose**: hedge-fund and PM strategy playbooks.
- **Workflows**: `equity-long-short`, `long-biased`, `vibe-trading-event-driven`, `macro`, `quant`, `multi-strategy`.
- **Scenarios**: "long/short pair construction", "concentrated long-biased book", "event-driven special sits", "macro regime trading", "systematic quant strategy", "pod multi-strategy capital allocation".
- **Triggers**: long/short, pair trade, hedge fund, PM playbook, market neutral, gross/net leverage, multi-strategy, pod, event-driven.
- **Combine with (legacy)**: `vibe-trading-cross-market-strategy` (SignalEngine), `vibe-trading-strategy-generate` (backtest), `idea-generation`, `swarm-orchestrator` (multi-agent IC).
- **⚠️ Voice/tone**: strong PM persona voice is an analytical lens to force factor-aware discipline — not the platform's official stance, not a trading mandate.

---

## Subagent → Skill Trigger Map

How each subagent triggers the new skills (loaded via the `skill` tool by that subagent when a matching intent arrives):

| Subagent | llmquant skills it primarily triggers |
|---|---|
| `market-router` | `llmquant-commodities`, `llmquant-crypto`, `llmquant-macro`, `llmquant-rates-fx`, `llmquant-prediction-markets` (data routing) |
| `market-researcher` | `llmquant-commodities`, `llmquant-credit`, `llmquant-etfs`, `llmquant-events`, `llmquant-market-intelligence`, `llmquant-investor-lenses`, `llmquant-prediction-markets` |
| `equity-research` | `llmquant-equities`, `llmquant-events`, `llmquant-investor-lenses`, `llmquant-portfolio`, `llmquant-market-intelligence` |
| `earnings-reviewer` | `llmquant-equities`, `llmquant-events` |
| `financial-analysis` | `llmquant-credit`, `llmquant-equity-derivatives`, `llmquant-etfs`, `llmquant-options` |
| `factor-researcher` | `llmquant-crypto`, `llmquant-macro`, `llmquant-options`, `llmquant-rates-fx`, `llmquant-risk`, `llmquant-equity-derivatives` |
| `wealth-management` | `llmquant-portfolio`, `llmquant-portfolio-lab`, `llmquant-risk`, `llmquant-investor-lenses`, `llmquant-macro` |
| `valuation-reviewer` | `llmquant-portfolio-lab`, `llmquant-risk` |
| `backtest-builder` | `llmquant-strategies`, `llmquant-options` (backtest workflows) |
| `alpha-researcher` | `llmquant-strategies` (quant workflow) |
| `swarm-orchestrator` | `llmquant-strategies` (multi-strategy pod) |
| `model-builder` / `investment-banking` / `pitch-agent` / `private-equity` / `operations` / `fund-admin` / `gl-reconciler` / `month-end-closer` / `statement-auditor` / `kyc-screener` / `meeting-prep-agent` | rarely trigger llmquant skills (institutional/document workflows — no overlap) |

---

## Cross-Reference: Legacy ↔ New Skill Matrix

For the overlapping legacy skills, load BOTH and let the new workflow orchestrate while the legacy skill supplies the deep methodology:

| Legacy skill (methodology) | New llmquant skill (workflow) | How they combine |
|---|---|---|
| `vibe-trading-commodity-analysis` | `llmquant-commodities` | Legacy generates directional signal; new produces the curve/inventory/macro brief |
| `vibe-trading-credit-analysis` | `llmquant-credit` | Legacy supplies rating/spread methodology; new runs issuer/HY stress workflows |
| `vibe-trading-crypto-derivatives` / `vibe-trading-perp-funding-basis` | `llmquant-crypto` | Legacy has funding/derivatives mechanics; new has regime/token/perp monitoring workflows |
| `stock-deep-dive` / `thesis-tracker` | `llmquant-equities` | Legacy does the deep综合 path; new adds the five-lens scoring rubric + take-profit lab |
| `vibe-trading-convertible-bond` | `llmquant-equity-derivatives` | Legacy is the 三维估值; new is the single-stock derivative playbook |
| `vibe-trading-etf-analysis` / `vibe-trading-us-etf-flow` | `llmquant-etfs` | Legacy does selection/fees/flows; new does holdings overlap + concentration |
| `earnings-preview` / `vibe-trading-corporate-events` / `catalyst-calendar` | `llmquant-events` | Legacy supplies preview/event mechanics; new supplies event-brief/tracker workflows |
| `vibe-trading-macro-analysis` / `vibe-trading-global-macro` | `llmquant-macro` / `llmquant-rates-fx` | Legacy has cycle/CB theory; new has dashboard/preview/portfolio-impact + curve/carry workflows |
| `vibe-trading-sentiment-analysis` / `morning-note` | `llmquant-market-intelligence` | Legacy has sentiment indicators; new has the reusable signal views |
| `vibe-trading-options-strategy` / `vibe-trading-options-payoff` / `vibe-trading-options-advanced` | `llmquant-options` | Legacy has pricing/Greeks/payoff theory; new has IV-rank/Greeks-dashboard/P&L/vol-surface workflows |
| `thesis-tracker` / `portfolio-monitoring` | `llmquant-portfolio` | Legacy has quarterly re-check discipline; new has profile/thesis/watchlist/alert workspace |
| `portfolio-rebalance` / `vibe-trading-risk-analysis` | `llmquant-portfolio-lab` | Legacy has drift/VaR; new has exposure-map + what-if simulator |
| `vibe-trading-risk-analysis` / `vibe-trading-correlation-regime` / `vibe-trading-hedging-strategy` | `llmquant-risk` | Legacy has VaR/regime/hedge-ratio; new has fear-score/VIX/hedge-advisor/research-health |
| `vibe-trading-cross-market-strategy` / `vibe-trading-strategy-generate` | `llmquant-strategies` | Legacy has SignalEngine/backtest; new has PM playbook mental models + risk mgmt |
| `vibe-trading-behavioral-finance` / `vibe-trading-management-deep-dive` | `llmquant-investor-lenses` | Legacy has bias checklist/management scoring; new has persona reasoning frames |

---

## Evidence Contract (applies to all 17)

All 17 skills enforce the same LLMQuant Data contract, which aligns with the project's `backtest-discipline.md` rules:

1. **Source grounding** — external facts come from `llmquant-data` MCP tools (or user-provided data), never from memory.
2. **Freshness** — report filing dates, report periods, observation dates, price timestamps, holdings `as_of_date`, and stale notices.
3. **Fallback** — if a required input is unavailable, name the missing input and continue only with retrieved evidence; do not invent weights, spreads, odds, or valuations.
4. **Boundary honesty** — separate company-disclosed facts from interpretation; label inference separately.
5. **Research only** — no live-trade or execution actions; outputs are drafts for human review.

These rules are consistent with and subordinate to `.opencode/instructions/data-priority.md`, `backtest-discipline.md`, and `memory-protocol.md`.
