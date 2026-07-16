# Example Cookbooks

Each cookbook is a domain-specific starter kit. Questions are meant to be asked via **Wealth-Guide** — the single entry-point agent — which routes to the correct subagent internally.

## Using the Cookbooks

Start a session with Wealth-Guide, then ask any question from `questions.md`:

```bash
opencode --agent wealth-guide
```

Wealth-Guide will route your question to the appropriate subagent(s).

## Available Cookbooks

### Institutional (18)
| Cookbook | Routes to subagent |
|---|---|
| `earnings-reviewer/` | earnings-reviewer |
| `equity-research/` | equity-research |
| `financial-analysis/` | financial-analysis |
| `fund-admin/` | fund-admin |
| `gl-reconciler/` | gl-reconciler |
| `investment-banking/` | investment-banking |
| `kyc-screener/` | kyc-screener |
| `market-researcher/` | market-researcher |
| `meeting-prep-agent/` | meeting-prep-agent |
| `model-builder/` | model-builder |
| `month-end-closer/` | month-end-closer |
| `operations/` | operations |
| `pitch-agent/` | pitch-agent |
| `private-equity/` | private-equity |
| `statement-auditor/` | statement-auditor |
| `valuation-reviewer/` | valuation-reviewer |
| `wealth-management/` | wealth-management |
| `explore/` | (generic code exploration) |

### Quantitative Research (5 — New)
| Cookbook | Routes to subagent |
|---|---|
| `alpha-researcher/` | alpha-researcher |
| `backtest-builder/` | backtest-builder |
| `factor-researcher/` | factor-researcher |
| `market-router/` | market-router |
| `swarm-orchestrator/` | swarm-orchestrator |

### End-to-End (1 — New)
| Cookbook | Description |
|---|---|
| `wealth-guide-e2e/` | Cross-domain questions requiring multiple subagents |
