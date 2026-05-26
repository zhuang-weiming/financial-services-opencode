---
name: variance-commentary
description: Write flux commentary for every P&L and balance-sheet line over threshold — current vs prior period and vs budget, with the driver explained from underlying activity. Use for the month-end close package and management reporting.
---

# Variance commentary

Given current-period actuals, prior-period actuals, and budget for the same scope, produce a commentary table.

## Required Inputs

| Input | Format | Example |
|-------|--------|---------|
| **Current-period actuals** | CSV, XLSX, or user-provided data with P&L / BS line items and amounts | — |
| **Prior-period actuals** | Same structure as current-period | — |
| **Budget** | Same structure as current-period | — |
| **Materiality threshold** | Amount or % (default: 5% of line or fixed floor) | "$10,000 or 5%" |
| **Always-comment list** | List of account names that always require commentary | ["Revenue", "Headcount cost", "Cash"] |
| **Period** | YYYY-MM or YYYY-MM-DD | "2026-03" |

## Threshold

Flag a line for commentary if **either** is true:

- Absolute variance ≥ the firm's materiality threshold (use the provided value; default 5% of the line or a fixed floor, whichever is greater)
- The line is on the "always comment" list (revenue, headcount cost, cash)

## For each flagged line

| Column | Content |
|---|---|
| **Line** | Account or caption |
| **Current / Prior / Budget** | The three values |
| **Δ vs prior** and **Δ vs budget** | Amount and % |
| **Driver** | One sentence explaining the movement from underlying activity — not a restatement of the number |

A driver explains *why*, not *what*: "Cloud spend up $1.2M on incremental GPU reservations for the May launch" — not "Cloud spend increased $1.2M (18%)."

## Sourcing the driver

Look at the activity behind the line (journal-source breakdown, vendor mix, headcount delta, volume × rate). Ask the user to provide GL data or use available MCPs. If the driver isn't clear from the data, write "driver unclear — flag for controller" rather than inventing one.

## Output

The commentary table plus a short narrative (3–5 sentences) summarizing the period's biggest movers.

## Error Handling

| Error | Response |
|-------|----------|
| Line items don't match across periods | Flag "Account mismatch — verify same chart of accounts across periods" |
| Missing prior-period data for a line | Flag "Prior period data missing — cannot compute variance" |
| Missing budget data | Flag "Budget data missing for this period" and skip vs-budget variance |
| Materiality threshold not provided | Use default (5% of line or $5,000 floor) and note in output |
| Variance calculation produces NaN | Flag "Calculation error — check source data types" |
