# GL-Reconciler Agent — Example Questions

> **Routing trigger keywords:** GL recon, GL reconciliation, break trace, reconciliation, general ledger, subledger, position mismatch, trade date reconciliation

**Data Files:**
- `data/recon_data.csv` - Trade reconciliation data for trade date 2024-03-15
- `data/recon_breaks.json` - Breaks identified with suspected causes and status

---

## Question 1: Trade Date Reconciliation
```
Using data/recon_data.csv, reconcile the general ledger to subledger for trade date 2024-03-15.

Reference: data/recon_data.csv, data/recon_breaks.json (breaks[0], breaks[1])

Breaks identified in data/recon_breaks.json:
- AAPL-US position mismatch: GL 10,000 shares, Subledger 9,500 shares (variance: $50,000)
- MSFT-US missing dividend: GL $25,000, Subledger $0 (variance: $25,000)

Please:
1) Load data/recon_data.csv and data/recon_breaks.json
2) Classify each break by likely cause (timing, system drift, or reclass)
3) Provide root cause analysis for each break
4) Show the transaction-level evidence from the data
```

---

## Question 2: Fixed Income Coupon Reconciliation
```
Run a month-end reconciliation for our fixed income portfolio as of 2024-02-29.

Reference: data/recon_data.csv (CORP-BOND-01 row)

From data/recon_data.csv:
- Account: Accrued Interest
- GL Balance: $45,000
- Subledger Balance: $45,200
- Variance: -$200 (for Financials sector corporate bonds)

Trace the source of this $200 variance for corporate bonds in the Financials sector.

Additional data in data/recon_breaks.json may show patterns from prior periods.
```

---

## Question 3: Cash and Securities Breakdown
```
Our daily reconciliation for 2024-03-20 shows cash position variance of $2.3 million.

Reference: data/recon_data.csv (USD cash account rows), data/recon_breaks.json

Using the data files:
1) Identify which accounts have variances
2) Calculate total variance by asset class
3) Flag any accounts exceeding the $10,000 threshold
4) Draft the exception report for controller review
```