# Example Cookbooks

Each cookbook is a domain-specific starter kit. Questions are meant to be asked via **Wealth-Guide** — the single entry-point agent — which routes to the correct subagent internally.

## Using the Cookbooks

Start a session with Wealth-Guide, then ask any question from `questions.md`:

```bash
opencode --agent wealth-guide
```

Wealth-Guide will route your question to the appropriate subagent(s).

---

## Cookbook Index

### Institutional (19 subagents)

| # | Cookbook | Routes to subagent | Trigger keywords |
|---|:---|---|:---|
| 1 | `earnings-reviewer/` | `earnings-reviewer` | earnings, quarterly results, Q1/Q2/Q3/Q4, post-earnings |
| 2 | `equity-research/` | `equity-research` | initiating coverage, model update, catalyst calendar, thesis track |
| 3 | `financial-analysis/` | `financial-analysis` | 3-statement model, DCF, LBO, comps, competitive analysis |
| 4 | `fund-admin/` | `fund-admin` | NAV tie-out, accrual schedule, roll-forward, variance commentary |
| 5 | `gl-reconciler/` | `gl-reconciler` | GL recon, break trace, reconciliation |
| 6 | `investment-banking/` | `investment-banking` | pitch deck, CIM, teaser, process letter, buyer list, merger model |
| 7 | `kyc-screener/` | `kyc-screener` | KYC, onboarding, AML screening, watchlist |
| 8 | `market-researcher/` | `market-researcher` | sector overview, industry deep dive, competitive landscape |
| 9 | `meeting-prep-agent/` | `meeting-prep-agent` | client review, meeting prep, briefing pack, investment proposal |
| 10 | `model-builder/` | `model-builder` | DCF model, LBO model, 3-statement model, trading comps |
| 11 | `month-end-closer/` | `month-end-closer` | month-end close, close package, accrual schedule |
| 12 | `operations/` | `operations` | AI readiness, DD checklist, deal sourcing, value creation plan |
| 13 | `pitch-agent/` | `pitch-agent` | pitch deck, comps analysis, DCF, LBO, IB check deck |
| 14 | `private-equity/` | `private-equity` | IC memo, deal screen, deal sourcing, buyer list |
| 15 | `statement-auditor/` | `statement-auditor` | statement audit, LP statement, model audit, NAV tie-out |
| 16 | `valuation-reviewer/` | `valuation-reviewer` | valuation review, returns analysis, stress-test |
| 17 | `wealth-management/` | `wealth-management` | client report, financial plan, portfolio rebalance, tax-loss harvesting |
| 18 | `wif-framework/` | `wealth-management` | WIF (US), wealth investment framework, asset allocation portfolio, fund advisory methodology, portfolio health, phase assessment, F29, VIXTERM |
| 19 | **`wif-ashare/`** | `wealth-management` | **A股WIF, MCI, PMI M2, MA60趋势, 沪深300配置, A股象限, A股资产配置** |

### Quantitative Research (5 subagents)

| # | Cookbook | Routes to subagent | Trigger keywords |
|---|:---|---|:---|
| 20 | `alpha-researcher/` | `alpha-researcher` | alpha zoo, factor bench, alpha family, IC/IR |
| 21 | `backtest-builder/` | `backtest-builder` | backtest, strategy backtest, walk-forward, signal test |
| 22 | `factor-researcher/` | `factor-researcher` | factor analysis, IC/IR, quantile backtest, factor decomposition |
| 23 | `market-router/` | `market-router` | crypto (BTC/ETH), A-share (600519), forex (EURUSD), multi-market |
| 24 | `swarm-orchestrator/` | `swarm-orchestrator` | swarm, investment committee, multi-agent team, macro forum |
| 25 | `alpha-engine-v21/` | `alpha-researcher` + `alpha-engine-v21` skill | V21, lazybear, WaveTrend, WT1, WT2, low-vol A-share, Deflated Sharpe Ratio, 懒熊振荡器, 低波动 A 股 |

### Utility (2)

| # | Cookbook | Description |
|---|:---|---|
| 26 | `explore/` | Codebase exploration (not a routed subagent) |
| 27 | `wealth-guide-e2e/` | Cross-domain questions requiring multiple subagents in parallel |

---

## Routing Verification

Each `questions.md` file includes a header line noting the **routing trigger keywords** that Wealth-Guide uses to dispatch the question to the correct subagent. To verify routing:

1. Read the trigger keywords in the header
2. Check that the questions contain those keywords
3. Confirm against the [routing decision matrix](../.opencode/instructions/wealth-guide-router.md)

### Example routing trace

```
User: "Run a backtest on CSI 300 momentum strategy from 2023 to 2025"
                              ^^^^^^^^
Wealth-Guide sees "backtest" → routes to backtest-builder ✅
```

```
User: "Review CloudSoft IC memo for investment committee"
                              ^^^^^^^^
Wealth-Guide sees "IC memo" → routes to private-equity ✅
```

## Parallel Dispatch (Cross-Domain)

For questions spanning multiple domains, Wealth-Guide dispatches to multiple subagents simultaneously. See `wealth-guide-e2e/questions.md` for examples.

Example: *"Analyze NVDA's latest earnings, build a DCF model, and compare against AMD"*
→ dispatches to `earnings-reviewer` + `model-builder` + `market-researcher` in parallel.

### WIF Framework Cross-Domain Examples

| Domain Pattern | Parallel dispatch |
|:---|---|
| US WIF phase + A-Share WIF quadrant | `wealth-management` → load both `wif-fund-advisory` + `wif-ashare-advisory` |
| A-Share WIF + alpha research + backtest | `market-router` (data) + `alpha-researcher` + `backtest-builder` |
| US WIF rebalance + tax harvesting | `wealth-management` → `wif-fund-advisory` + `tax-loss-harvesting` |
| A-Share WIF + macro analysis | `wealth-management` → `wif-ashare-advisory` + `global-macro` |
