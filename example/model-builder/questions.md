# Model-Builder Agent Example Questions

**Data Files:**
- `data/historical_data.csv` - Historical financial data
- `data/model_assumptions.json` - Model assumptions

---

## Question 1: Build 3-Statement Model
```
Build a 3-statement model for Sample Corp.

Reference: data/historical_data.csv, data/model_assumptions.json

From data/historical_data.csv:
- Q1 FY23 to Q1 FY24 quarterly data
- Revenue range: $2.1M - $2.6M
- EBITDA margin: ~24%

From data/model_assumptions.json:
- Revenue growth: 8%
- EBITDA margin: 24%
- Tax rate: 21%
- Capex: 8% of revenue
- Working capital: 7% of revenue

Please:
1) Build integrated IS/BS/CF model
2) Link all three statements
3) Balance the model
4) Add ratio analysis
```

---

## Question 2: Forecast Validation
```
Validate the Q1 FY24 forecast assumptions.

Reference: data/historical_data.csv

From data/historical_data.csv:
- Q1 FY24 Revenue: $2.62M
- Q1 FY24 EBITDA: $650K (25% margin)
- Q1 FY24 Cash Flow: $610K

Please:
1) Compare to historical trends
2) Assess margin sustainability
3) Flag any assumption changes
4) Update model if needed
```