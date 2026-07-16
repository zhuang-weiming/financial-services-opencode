# Fund-Admin Agent — Example Questions

> **Routing trigger keywords:** NAV tie-out, NAV tieout, accrual schedule, roll-forward, variance commentary, fund admin, fund administration, cash flow projection

**Data Files:**
- `data/lp_capital_accounts.csv` — LP capital accounts
- `data/accrual_schedule.json` — Accrual schedule
- `data/nav_tieout.json` — NAV tieout
- `data/roll_forward.json` — Roll-forward
- `data/cash_flow_projection.json` — Cash flow projection

---

## Question 1: NAV Tieout
```
Tie out LP statement to fund NAV pack.

Reference: data/nav_tieout.json, data/lp_capital_accounts.csv

From data/nav_tieout.json:
- NAV Date: 2024-03-31
- Total NAV: $45M
- Harborview: Cleared
- Meridian: $50K variance, pending

From data/lp_capital_accounts.csv:
- Harborview: $25M commitment, NAV $28M
- Meridian: $15M commitment, NAV $16.5M

Please:
1) Recompute LP capital accounts
2) Identify variance source
3) Clear or escalate
4) Confirm final NAV
```

## Question 2: Accrual Schedule Review
```
Review March accrual schedule.

Reference: data/accrual_schedule.json

From data/accrual_schedule.json:
- Management Fee: $125K (pending)
- Audit Fee: $45K (approved)
- Legal Fee: $15K (pending)

Please:
1) Validate entry amounts
2) Cite support documentation
3) Draft journal entries
4) Flag for controller approval
```

## Question 3: Build accrual schedule for month-end close
```
Build the period-end accrual schedule for month-end close. For each accrual, compute the entry, cite the support, and draft the journal entry.

Reference: data/accrual_schedule.json, data/roll_forward.json

Please:
1) List all required accruals for the period
2) Compute each accrual amount with supporting documentation
3) Draft journal entries for controller approval
4) Flag any items requiring manual review
```
