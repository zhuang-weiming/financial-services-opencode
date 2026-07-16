# KYC-Screener Agent Example Questions

**Data Files:**
- `data/client_onboarding.csv` - Client onboarding records
- `data/watchlist_results.json` - Watchlist screening results

---

## Question 1: Client Onboarding Screening
```
Screen new client Harborview Endowment against watchlists.

Reference: data/client_onboarding.csv (row 1), data/watchlist_results.json

From data/client_onboarding.csv:
- Client: Harborview Endowment
- Risk Rating: Medium
- Account Type: Institutional

From data/watchlist_results.json (index 1):
- Name: Maria Santos
- Type: Individual
- List: EU Sanctions
- Match Confidence: 72%
- Status: cleared

Please:
1) Parse the client onboarding record
2) Cross-reference against watchlist results
3) Assign risk rating based on firm rules
4) Flag any items requiring enhanced due diligence
```

---

## Question 2: Enhanced Due Diligence Review
```
Review Alpha Trading Ltd for potential high-risk designation.

Reference: data/client_onboarding.csv, data/watchlist_results.json

From data/watchlist_results.json:
- Name: Alpha Trading Ltd
- Type: Entity
- List: FATF High-Risk
- Match Confidence: 88%
- Status: enhanced_due_diligence

Please:
1) Document the watchlist match details
2) Apply firm KYC rules for high-risk entities
3) Determine required documentation
4) Draft escalation if needed
```

---

## Question 3: ['What', 'is', 'the', "firm's", 'enhanced', 'due']
```
What is the firm's enhanced due diligence procedure for PEPs?
```
