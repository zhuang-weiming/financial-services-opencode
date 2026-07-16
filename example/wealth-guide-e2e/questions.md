# Wealth-Guide End-to-End — Cross-Domain Questions

These questions require Wealth-Guide to dispatch to **multiple subagents** in parallel or sequence, then compose a unified answer.

### 1. "I want to build an investment thesis on NVDA. Analyze their latest earnings, build a DCF model, and compare against AMD."

**Expected routing:** `earnings-reviewer` (earnings analysis) + `model-builder` (DCF) + `market-researcher` (competitive landscape / comps)

### 2. "Screen for PE deals in fintech, then do a competitive analysis. Also check my portfolio for any overlaps."

**Expected routing:** `private-equity` (deal screening) + `market-researcher` (competitive landscape) + `operations` (portfolio monitoring)

### 3. "Research the momentum factor on CSI 300 using the alpha zoo, then backtest the top 10 alphas."

**Expected routing:** `alpha-researcher` (alpha bench) + `factor-researcher` (factor analysis) + `backtest-builder` (backtest)

### 4. "I need a client review meeting prep for the Smith family. Also check if there are any tax-loss harvesting opportunities."

**Expected routing:** `meeting-prep-agent` (client review prep) + `wealth-management` (tax-loss harvesting)

### 5. "Analyze BTC from both a technical analysis perspective and fundamental on-chain data. Also run the crypto research lab swarm."

**Expected routing:** `market-router` (data routing) + `swarm-orchestrator` (crypto_research_lab team)

### 6. "Close the books for March — run the month-end close, then audit the LP statements."

**Expected routing:** `month-end-closer` (close process) + `statement-auditor` (LP statement audit)

### 7. "What's the cross-asset outlook? Run the macro forum, global allocation committee, and equities desk."

**Expected routing:** `swarm-orchestrator` (multiple teams: macro_strategy_forum + global_allocation_committee + equity_research_team)

### 8. "I'm meeting a fintech startup investor next week. Prep me with a briefing pack, screen the space for deals, and build a list of strategic buyers."

**Expected routing:** `meeting-prep-agent` (meeting prep) + `private-equity` (deal screening) + `investment-banking` (buyer list)
