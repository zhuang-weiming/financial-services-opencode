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

---

## Premier 客户跨域场景（额外 5 个）

这些场景面向高端个人投资者（Premier），需要 wealth-guide 跨域调度并综合输出。

### P1. "我现有 500 万资金，想做一个完整的投资方案——从风险测评到宏观判断到资产配置到选品再到调仓"

**Expected routing:** `wealth-management` (风险测评/财务规划) + `market-researcher` (宏观/趋势) + `market-router` (多市场数据) + `wif-framework` (资产配置/WIF 阶段判断) + `pitch-agent` (ETF 组合方案构建)

**跨域流程:** 风险测评(wealth-management) → 宏观判断(market-researcher + market-router) → 阶段判断(wif-framework) → 配置方案(pitch-agent) → 最终由 wealth-guide 整合输出完整投资计划书

### P2. "我持有的某只股票（贵州茅台/苹果）已经盈利不少，现在该卖了吗？帮我从财报、估值、因子和行为偏误几个角度综合判断"

**Expected routing:** `earnings-reviewer` (最新财报分析) + `model-builder` (估值模型/DCF) + `factor-researcher` (因子暴露分析) + `behavioral-finance` (行为偏误诊断——处置效应/过度自信)

**跨域流程:** 财报分析(earnings-reviewer) → 估值更新(model-builder) → 因子暴露检查(factor-researcher) → 行为偏误检查(behavioral-finance) → wealth-guide 综合给出持有/减仓/清仓建议

### P3. "年底了，帮我做年度投资回顾和税务优化——复盘全年持仓表现、做税收亏损收割、更新投资理念检视、展望明年"

**Expected routing:** `wealth-management` (年度回顾 + TLH 税收亏损收割) + `equity-research` (持仓复盘与论文更新) + `meeting-prep-agent` (年度汇报材料) + `market-researcher` (来年趋势展望)

**跨域流程:** 持仓复盘(equity-research) → TLH 方案(wealth-management) → 来年展望(market-researcher) → 汇报材料(meeting-prep-agent) → wealth-guide 整合输出年度回顾报告

### P4. "帮我验证一个投资想法——我发现在某些市场条件下，高股息+低波动组合表现特别好。帮我做因子回测、策略构建和实盘建议"

**Expected routing:** `alpha-researcher` (因子研究: 红利+低波因子 IC/IR) + `factor-researcher` (因子组合构建/相关性分析) + `backtest-builder` (策略回测/参数优化) + `wealth-management` (实盘落地方案)

**跨域流程:** 因子验证(alpha-researcher) → 组合构建(factor-researcher) → 回测优化(backtest-builder) → 实盘建议(wealth-management) → wealth-guide 输出"研究→回测→实盘"全链路报告

### P5. "我收到一份 PE 跟投邀请，同时也看中一个 REITs 和一个量化策略基金，想比较这三种另类投资方案，选出最适合我的那个"

**Expected routing:** `private-equity` (PE 跟投评估) + `financial-analysis` (REITs 分析 + 财务对比) + `backtest-builder` (量化策略回测评估) + `wealth-management` (组合影响分析)

**跨域流程:** 逐个评估(private-equity + financial-analysis + backtest-builder) → 横向对比(wealth-guide 综合) → 组合影响分析(wealth-management) → wealth-guide 给出推荐排序
