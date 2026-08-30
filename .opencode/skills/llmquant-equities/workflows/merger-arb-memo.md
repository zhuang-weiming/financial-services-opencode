---
name: Merger-Arb Memo
description: Build a catalyst-bound merger-arbitrage memo using LLMQuant Data filings, prices, and ownership context.
input_data_source: LLMQuant Data
pack: workflows
---

# Merger-Arb Memo

## Purpose

Create a deal memo that frames merger-arbitrage risk, spread context, regulatory and shareholder issues, financing, timing, downside, and evidence gaps.

---

## Input Data Source

Use **LLMQuant Data** as the input data source for company filings, price history, 13F ownership, and contextual research. State which LLMQuant Data capabilities were used, cite filing dates and price ranges, and do not invent data that was not retrieved.

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
- State the filing date and period of report for each filing used.
- State the price history range used for spread or downside context.
- Do not claim a definitive current deal spread unless current deal terms and latest prices are retrieved or supplied by the user.

Fallback:
- If deal terms are not in retrieved filings, ask the user for terms or state the missing input.
- If regulatory details are absent, list them as evidence gaps.

Output:
- Deal snapshot
- Spread/downside framework
- Probability drivers
- Risk table
- Data used

---

## Workflow

1. Identify target, acquirer, consideration, announced terms, and expected close date from user input or retrieved filings.
2. Pull relevant filings for target and acquirer where available.
3. Pull price history for target and acquirer to frame pre-deal unaffected price and post-announcement trading.
4. Pull 13F holders when shareholder vote, activism, or arbitrage crowding matters.
5. Separate hard evidence from assumptions about antitrust, financing, shareholder approval, and timing.
6. Present the trade as an expected-value problem, not a certainty.

---

## Output Format

Use:

1. **Deal Snapshot**
2. **Current Setup / Spread Context**
3. **Probability Tree**: regulatory, financing, shareholder, timing, litigation.
4. **Downside Case**
5. **Key Evidence**
6. **Open Diligence Items**
7. **Data Used**

---

## Guardrails

- Do not fabricate deal terms.
- Do not give legal conclusions.
- Do not claim borrow availability unless data is provided.
- Do not use stale prices without labeling their date range.
