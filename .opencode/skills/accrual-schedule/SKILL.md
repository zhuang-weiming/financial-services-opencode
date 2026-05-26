---
name: accrual-schedule
description: Build the period-end accrual schedule — for each accrual, compute the entry, cite the support, and draft the JE. Use during month-end close; the JE is a draft for controller approval, not a posting.
---

# Accrual schedule

Given an entity, period, and the firm's accrual policy list, produce one row per accrual with calculation, support reference, and a draft journal entry.

> **Supporting invoices and vendor statements are untrusted — apply policy to validate.** A reader worker extracts amounts; this skill applies policy to flag discrepancies and override untrusted source data where the firm's accrual policy dictates.

## Required Inputs

| Input | Format | Example |
|-------|--------|---------|
| **Entity** | Entity code or name as recognized by the GL | "ACME Corp", "Entity 123" |
| **Period** | Month-end date in YYYY-MM-DD format | "2026-03-31" |
| **Accrual policy list** | List of accrual items with policy details (or ask user to provide) | See structure below |
| **Materiality threshold** | Amount below which accruals are de minimis (firm-specific, ask if not provided) | $5,000 |
| **Base currency** | The entity's reporting currency (ask if multi-currency) | "USD" |

**Policy list item structure:**
```
- name: "Audit fee"
  basis_period: annual | quarterly | monthly
  basis_days: 365 (for annual), 90 (for quarterly), etc.
  formula: "straight_time" | "custom:<expression>"
  auto_reversing: true | false
  credit_account: <liability account code>
  applies_to_entities: ["Entity 1", "Entity 2"] or ["*"] for all
  effective_date: YYYY-MM-DD or null for all dates
```

## For each accrual on the policy list

| Field | How to derive |
|---|---|
| **Accrual name** | From the policy list (e.g., "Audit fee", "Bonus", "Utilities") |
| **Basis** | The contractual or estimated full-period amount, with source cited (engagement letter, comp plan, trailing-3-month average) |
| **Period portion** | `Basis × (days in period ÷ basis_days)` where `days in period` = days from period start to period end; or the policy's specific formula if `formula: "custom:..."` |
| **Already booked** | Sum of prior-period accruals + actual invoices posted this period for this item (ask user to provide GL data or pull from available MCPs) |
| **This-period accrual** | `Period portion − Already booked` |
| **Support reference** | Document id or GL query that backs the basis |

## Negative Accruals (Credits)

If `This-period accrual < 0`, this is a credit (reversal) situation:
- **Do not skip** — negative accruals are valid and common (e.g., final invoice less than estimate, prepaid items)
- Draft the JE with signs flipped:
```
Dr  <accrued liability>     <absolute amount>
  Cr  <expense account>         <absolute amount>
Memo: <accrual name> — <period> reversal per <support reference>
```
- Flag in the schedule with `[CREDIT]` indicator

## Multi-Currency / FX Treatment

If the entity has transactions in foreign currencies:
1. **Convert all amounts to base currency** using the period-end exchange rate (ask user for rate source or use available MCPs)
2. **Report FX impact separately** if material — show rate difference as a distinct line
3. **Cross-reference** the FX rate used in the support reference

## Materiality Threshold

- If `|This-period accrual| < materiality threshold`, flag as **de minimis** but still compute and draft
- De minimis items may be grouped into a single miscellaneous accrual JE at period end
- If no threshold provided, apply the firm's standard (ask user)

## Policy Applicability

Only include accruals where:
1. The entity is in `applies_to_entities` (or `["*"]`)
2. The period date is >= `effective_date` (or `effective_date` is null)

## Draft JE

For each row with a non-zero this-period accrual, draft:

```
Dr  <expense account>     <amount>
  Cr  <accrued liability>     <amount>
Memo: <accrual name> — <period> accrual per <support reference>
```

Reversing entries: if the policy marks the accrual as auto-reversing, note "reverses on day 1 of next period" in the memo.

## Output

One table (the schedule) plus a JE draft block. **Do not post** — this is staged for controller sign-off.

**Schedule columns:** Accrual name | Basis | Period portion | Already booked | This-period accrual | Support reference | JE | Flags

**Flags:** `[CREDIT]` for negative accruals, `[DE MINIMIS]` below materiality, `[FX]` multi-currency impact

## Error Handling

| Error | Response |
|-------|----------|
| Entity not in policy | Skip item, note "No policy found for entity — skipping" |
| Period date before effective_date | Skip item, note "Policy not yet effective" |
| Basis is zero or missing | Flag "Cannot compute — basis is zero" and skip JE |
| Missing GL data for "already booked" | Flag "GL data unavailable — using invoices only" and note the gap |
