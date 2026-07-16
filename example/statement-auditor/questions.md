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
