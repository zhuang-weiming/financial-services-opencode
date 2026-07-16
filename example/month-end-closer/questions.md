# Month-End-Closer Agent — Example Questions

> **Routing trigger keywords:** month-end close, close package, accrual schedule, roll-forward, variance commentary, month end

**Data Files:**
- `data/accrual_schedule.csv` — Accrual schedule
- `data/close_package.json` — Close status

---

## Question 1: Month-End Close Checklist
```
Run the month-end close for March 2024.

Reference: data/accrual_schedule.csv, data/close_package.json

From data/accrual_schedule.csv:
- Cash: $13.5M balanced
- Equity Positions: $2.5M balanced
- Accrued Expenses: $490K vs GL $485K = $5K variance

From data/close_package.json:
- Close Date: 2024-03-31
- Status: in_progress
- Variance Count: 2 (threshold $1K)
- Pending: Accrued Expenses ($5K), Prepaid Assets ($2.5K)

Please:
1) Review variance items
2) Determine root cause
3) Draft journal entries for approvals
4) Update close status
```

## Question 2: Accrual Schedule Review
```
Validate the accrual schedule for March.

Reference: data/accrual_schedule.csv

From data/accrual_schedule.csv:
- Accrued Expenses: $490K ending balance
- Variance vs GL: $5,000

Please:
1) Trace beginning balance
2) Verify additions and reductions
3) Identify variance driver
4) Propose adjustment
```

## Question 3: Run variance commentary for income statement
```
Run the variance commentary for the income statement vs budget for March.

Reference: data/close_package.json, data/accrual_schedule.csv

Please:
1) Compare actual P&L to budget by line item
2) Flag items exceeding 10% variance
3) Explain key drivers of significant variances
4) Draft commentary for management review
```
