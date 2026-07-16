# Valuation-Reviewer Agent — Example Questions

> **Routing trigger keywords:** valuation review, returns analysis, portfolio monitoring, IC memo review, LP reporting, GP package, stress-test valuation

**Data Files:**
- `data/valuation_data.csv` — Valuation comps
- `data/valuation_review.json` — Detailed valuation review

---

## Question 1: DCF Valuation Review
```
Challenge the Datadog DCF valuation.

Reference: data/valuation_data.csv, data/valuation_review.json

From data/valuation_data.csv:
- Datadog: Price $118, Target $140, Upside 18.6%
- WACC: 10.5%, Terminal Growth: 4.5%

From data/valuation_review.json:
- Base Case DCF: $140
- Bear Case: $115, Bull Case: $168
- Flags: Terminal growth upper range, margin assumption aggressive

Please:
1) Stress-test WACC assumptions
2) Challenge terminal growth rate
3) Test margin expansion sensitivity
4) Assess if current price reflects risk
```

## Question 2: Cloud Comp Set Valuation
```
Compare valuations across cloud infrastructure comps.

Reference: data/valuation_data.csv

From data/valuation_data.csv:
- Datadog: Upside 18.6%, WACC 10.5%
- Snowflake: Upside 25.7%, WACC 10.8%
- MongoDB: Upside 32.0%, WACC 11.2%

Please:
1) Normalize for growth differences
2) Rank by risk-adjusted upside
3) Identify best risk/reward
4) Draft allocation recommendation
```

## Question 3: Stress-test the DCF model with WACC adjustment
```
Stress-test the DCF model with a -100bps WACC adjustment to see valuation impact.

Reference: data/valuation_data.csv, data/valuation_review.json

Please:
1) Recalculate DCF value with lower WACC
2) Show sensitivity table (WACC ± 200bps × terminal growth ± 1%)
3) Identify which assumption has the highest leverage
4) Flag if the base case is too aggressive
```
