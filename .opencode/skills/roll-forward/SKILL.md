---
name: roll-forward
description: Build a roll-forward schedule for a balance-sheet account — beginning balance plus activity less reversals equals ending balance, with each component tied to GL. Use for month-end close packages and audit support.
---

# Roll-forward

Given an account (or account group), entity, and period, produce a roll-forward that ties beginning to ending.

## Required Inputs

| Input | Format | Example |
|-------|--------|---------|
| **Account (or account group)** | Account code or name, or comma-separated list for group | "2100", "2100,2101,2102" |
| **Entity** | Entity code or name | "ACME Corp" |
| **Period** | Period-end date in YYYY-MM-DD | "2026-03-31" |
| **Beginning balance** | Prior-period ending balance (or ask user to provide prior-period close package) | 1,250,000 |
| **GL data for activity** | Ask user to provide or use available MCPs | — |

## Structure

```
Beginning balance (per prior-period close)      X
  + Additions / new activity                    A
  + Accruals booked this period                 B
  − Reversals of prior accruals                (C)
  − Payments / settlements                     (D)
  ± Reclasses / adjustments                     E
  ± FX translation                              F
Ending balance (per GL at period end)           Y
```

## Tie each line

- **Beginning** — prior-period close package, or GL balance at prior-period end date.
- **Each activity line** — a GL query (account + date range + journal-source filter). Ask the user to provide the GL data or use available MCPs. Cite the query.
- **Ending** — GL balance at period-end date.

The schedule **must foot**: `X + A + B − C − D + E + F = Y`. If it doesn't, the gap is an unexplained item — surface it, don't plug it.

## Output

The roll-forward table with a "ties to" column citing the GL query or document for every line, plus a foot check (pass/fail and the unexplained delta if any).

## Error Handling

| Error | Response |
|-------|----------|
| Beginning balance not provided and prior-period close unavailable | Ask user for beginning balance or prior-period close package |
| Account not found in GL | Flag "Account not found — verify account code" |
| Schedule doesn't foot (unexplained delta) | Surface delta as "Unexplained: $X" — do not plug |
| FX translation component unclear | Flag "FX impact unclear — provide rate source" |
| Ending balance doesn't match GL | Flag "Ending balance mismatch — verify GL data" |
