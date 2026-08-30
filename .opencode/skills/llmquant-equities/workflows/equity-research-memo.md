---
name: Equity Research Memo
description: Compose filings, market data, ownership, and context into an evidence-first equity research memo using LLMQuant Data.
input_data_source: LLMQuant Data
pack: workflows
---

# Equity Research Memo

## Purpose

Produce a structured equity research memo for a public company. This workflow composes filings, price history, institutional ownership, and knowledge context into a clear investment view.

---

## Input Data Source

Use **LLMQuant Data** as the input data source for filings, market prices, 13F ownership, wiki context, and paper research. State which LLMQuant Data capabilities were used, cite returned dates or periods, and do not invent data that was not retrieved.

---

## LLMQuant Data Contract

Required data capabilities:
- SEC filing discovery
- SEC filing section retrieval
- equity price history

Optional data capabilities:
- ticker-level 13F holder data
- wiki knowledge search
- paper research search

Freshness:
- Use the latest available 10-K or 10-Q unless the user specifies a period.
- State filing dates, periods of report, price bar date range, and 13F ranking period.
- Do not imply current ownership or real-time fundamentals unless the tool provides that snapshot.

Fallback:
- If a filing section is unavailable, name the missing section and continue with retrieved sections.
- If 13F data has no holders in scope, state the universe limitation.

Output:
- Investment view
- Business and filing evidence
- Market and ownership context
- Risks
- Data used

---

## Workflow

1. Clarify ticker, horizon, and whether the user wants bullish, bearish, or neutral framing.
2. Read the latest relevant filing sections: business, risk factors, and MD&A.
3. Pull price history for drawdown, trend, volatility, and dividend/split context.
4. Pull 13F holders when sponsorship or crowding matters.
5. Use wiki or paper tools only to define concepts or support industry context.
6. Build the memo from retrieved evidence first, then interpretation.

---

## Output Format

Use:

1. **Rating / View**: bullish, bearish, neutral, or watchlist.
2. **Thesis Summary**: 3-5 evidence-backed bullets.
3. **Business Quality**
4. **Financial / Filing Evidence**
5. **Market Context**
6. **Ownership / Crowding**
7. **Key Risks**
8. **Variant Perception**
9. **Data Used**

---

## Guardrails

- Do not provide a price target unless the user asks and valuation assumptions are explicit.
- Do not mix filing evidence with memory.
- Do not overstate 13F timeliness.
- Do not present opinion as data.
