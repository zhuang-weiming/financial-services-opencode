# Fund-Admin Agent Example Questions

**Data Files:**
- `data/lp_capital_accounts.csv` - LP capital accounts
- `data/accrual_schedule.json` - Accrual schedule
- `data/nav_tieout.json` - NAV tieout
- `data/roll_forward.json` - Roll-forward
- `data/cash_flow_projection.json` - Cash flow projection

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

---

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

---

## Question 3: Cash Flow Projection
```
Review Q2 cash flow projection.

Reference: data/cash_flow_projection.json

From data/cash_flow_projection.json:
- Q1 Ending Cash: $13.3M
- Q2 Projected: $13.8M
- Assumptions: 6% growth, 18% margin

Please:
1) Validate assumptions
2) Check cash sufficiency for commitments
3) Flag any concerns
4) Update projection if needed
```