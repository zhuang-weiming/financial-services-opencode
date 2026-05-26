# Operations Agent Example Questions

**Data Files:**
- `data/portfolio_companies.csv` - Portfolio company data
- `data/ai_readiness.json` - AI readiness assessment

---

## Question 1: AI Readiness Scan
```
Scan portfolio for AI deployment opportunities.

Reference: data/portfolio_companies.csv, data/ai_readiness.json

From data/portfolio_companies.csv:
- TechCorp A: Score 7.5, Quick wins: Invoice automation, Chatbot
- TechCorp B: Score 4.2, Low priority
- TechCorp C: Score 8.2, Critical - Loan automation, Fraud detection
- TechCorp D: Score 5.8, Medium priority

From data/ai_readiness.json:
- Recommended: TechCorp C (Critical, 80 hrs)
- Secondary: TechCorp A (High, 40 hrs)

Please:
1) Rank companies by AI readiness
2) Identify highest-leverage quick wins
3) Estimate deployment hours
4) Draft deployment优先级 recommendation
```

---

## Question 2: Quarterly AI Roadmap
```
Build Q2 AI deployment roadmap.

Reference: data/ai_readiness.json

From data/ai_readiness.json:
- 4 companies reviewed
- 2 recommended for immediate action
- Total estimated hours tracked

Please:
1) Prioritize deployment sequence
2) Allocate operating partner time
3) Set milestones and check-ins
4) Draft stakeholder communication
```