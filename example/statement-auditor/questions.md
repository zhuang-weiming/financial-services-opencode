# Statement-Auditor Agent — Example Questions

> **Routing trigger keywords:** statement audit, LP statement, capital account, audit model, model audit, audit financials, NAV tie-out

**Data Files:**
- `data/audit_results.json` — Audit results
- `data/model_errors.csv` — Model errors detail

---

## Question 1: Model Audit
```
Audit the Tech Growth Model for errors.

Reference: data/audit_results.json, data/model_errors.csv

From data/audit_results.json:
- Audit ID: AUD-2024-0315
- Overall Status: FAIL
- 3 errors found, 1 warning
- Errors: broken links, hardcoded values, cross-check failures

From data/model_errors.csv:
- ERR-001: Revenue link broken (IS!B15)
- ERR-002: Terminal value hardcoded (DCF!C42)
- ERR-003: Cash tie-out variance $50K (CF!D25)

Please:
1) Verify each error against source data
2) Prioritize fixes by severity
3) Draft correction plan
4) Flag model for re-audit after fixes
```

## Question 2: Cross-Statement Consistency
```
Check 3-statement model for consistency.

Reference: data/audit_results.json

From data/audit_results.json:
- ERR-003: Cash tie-out off by $50,000

Please:
1) Trace cash flow from operations
2) Verify balance sheet cash linkage
3) Identify root cause of $50K variance
4) Propose fix to reconcile
```

## Question 3: Audit the LP capital accounts
```
Audit the LP capital accounts for the fund against the NAV pack.

Reference: data/audit_results.json

Please:
1) Recompute each LP's capital account from NAV components
2) Flag any line items that don't tie out
3) Trace breaks to their source transaction
4) Produce an exceptions report for the GP
```

## Question 4: Premier 持仓报表审计
```
请对我的 6 月持仓报表进行全面审计，交叉核对各账户记录。

Reference: data/premier_statement_audit.csv, data/audit_results.json

From data/premier_statement_audit.csv:
- 4 个账户（富途/盈透/OKX/招行）的 6/30 持仓数据
- 我的记录 vs 券商记录对比
- 3 处差异：盈透（NVDA 和现金）、OKX（ETH）

From data/audit_results.json:
- 参考审计格式和错误分类

Please:
1) 逐笔核实每个账户/每项资产的一致性
2) 对 3 处差异做重要性评估（金额/总资产占比）
3) 对每处差异做根源分析（可能的原因和处理步骤）
4) 检查是否存在以下问题：
   - 未结算交易导致的时间差差异
   - 费用/税费扣收未记录
   - 汇率换算差异
   - 分红/拆股/转股未同步
5) 汇总生成一份审计报告：通过/有条件通过/不通过
6) 如果差异总金额超过总资产 0.1%（约 $1,400），建议纠偏措施
```

## Question 5: 基金年报审计要点
```
请指导我如何读基金年报中的审计意见和关键数据。

Reference: data/premier_statement_audit.csv, data/audit_results.json

从基金年报（假设数据，非从文件读取）：

某基金年报的关键信息：
- 审计意见：无保留意见
- 基金总资产：9.8 亿
- 基金净资产：9.2 亿
- 持有人结构：机构 65%，个人 35%
- 前十大持仓占比：42%
- 年换手率：185%
- 管理费收入：1380 万
- 托管费：92 万
- 交易佣金：215 万

Please:
1) 解读审计意见类型（无保留/保留/否定/无法表示意见）的含义
2) 分析基金的持有人结构，机构占比高是好事吗？
3) 前十大持仓集中度 42% —— 是否过度集中？
4) 年换手率 185% —— 属于什么水平？对费率和业绩有什么影响？
5) 交易佣金 215 万 vs 管理费 1380 万 —— 隐性成本占比多少？
6) 对比审计后的财务数据与基金公司宣传的数据是否一致
7) 给 Premier 投资者列出读年报的 5 个检查要点
```
