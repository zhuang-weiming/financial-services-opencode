# Swarm-Orchestrator Agent — Example Questions

> **Routing trigger keywords:** swarm, multi-agent team, investment committee, global equities desk, macro forum, quant strategy desk, multi-perspective analysis

**Data Files:**
- `data/swarm_config.json` — Swarm team configuration and presets
- `data/portfolio_current.json` — Current portfolio holdings for committee review

---

## Question 1: Investment Committee on AAPL
```
Convene an investment committee to analyze AAPL's current investment merits.

Reference: data/swarm_config.json, data/portfolio_current.json

From data/swarm_config.json:
- Available teams: investment_committee, global_equities_desk, macro_strategy_forum, quant_strategy_desk
- Investment committee team members: fundamental analyst, technical analyst, risk officer, sector specialist

Please:
1) Launch the investment_committee swarm team
2) Each member should analyze AAPL from their perspective
3) Synthesize findings into a buy/hold/sell recommendation
4) Highlight areas of agreement and disagreement among members
```

## Question 2: Global Equities Desk on Market Conditions
```
Run the global equities desk team to analyze current market conditions and identify actionable opportunities.

Reference: data/swarm_config.json

Please:
1) Activate the global_equities_desk swarm
2) Have regional specialists cover US, Europe, and Asia
3) Cross-asset analyst reviews fixed income and FX implications
4) Output a consolidated view with top 3 trade ideas
```

## Question 3: Macro Forum on Q3 GDP Outlook
```
Launch the macro strategy forum to debate Q3 GDP outlook and its implications for asset allocation.

Reference: data/swarm_config.json, data/portfolio_current.json

Please:
1) Convene the macro_strategy_forum team
2) Each economist presents their GDP forecast view
3) Debate implications for equities, bonds, and commodities
4) Produce a consensus asset allocation tilt recommendation
```
