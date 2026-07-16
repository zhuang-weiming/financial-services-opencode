# Equity-Research Agent — Example Questions

> **Routing trigger keywords:** earnings analysis, initiating coverage, coverage initiation, morning note, thesis track, catalyst calendar, model update, coverage update

**Data Files:**
- `data/coverage_universe.csv` — Coverage universe with valuation metrics
- `data/research_report.json` — Sample research report

---

## Question 1: Initiating Coverage Analysis
```
Initiate coverage on Datadog (DDOG-US) based on the coverage universe data.

Reference: data/coverage_universe.csv, data/research_report.json

From data/coverage_universe.csv:
- Revenue FY0: $2.1B
- Growth Rate: 45%
- EBITDA Margin: 22%
- WACC: 10.5%
- Terminal Growth: 4.5%

From data/research_report.json:
- Rating: Buy
- Target Price: $140
- Current Price: $118
- Upside: 18.6%

Please:
1) Analyze the business model and growth drivers
2) Build DCF valuation with assumptions
3) Compare to SaaS comps set
4) Make investment recommendation
```

## Question 2: Compare Cloud Infrastructure Plays
```
Compare Snowflake vs Datadog vs Elastic for sector allocation.

Reference: data/coverage_universe.csv

From data/coverage_universe.csv:
- Snowflake: Revenue $3.2B, Growth 50%, WACC 10.8%
- Datadog: Revenue $2.1B, Growth 45%, WACC 10.5%
- Elastic: Revenue $420M, Growth 30%, WACC 10.5%

Please:
1) Normalize metrics for comparison
2) Score relative to growth/quality
3) Recommend sector weighting
4) Identify best-in-class entry point
```

## Question 3: Run a quick comparable analysis
```
Run a quick comparable analysis on the SaaS coverage universe to identify relative value.

Reference: data/coverage_universe.csv

Please:
1) Calculate EV/Revenue and EV/EBITDA multiples
2) Sort by growth-adjusted valuation
3) Flag outliers on either cheap/expensive side
4) Recommend top pick based on risk/reward
```
