---
name: ETF Overlap Report
description: Compare ETF holdings, concentration, and exposure overlap using LLMQuant Data ETF tools.
input_data_source: LLMQuant Data
pack: data
---

# ETF Overlap Report

## Purpose

Compare one or more ETFs for holdings overlap, concentration risk, issuer/profile context, sector or country exposure, and stale regulatory snapshot limitations.

---

## Input Data Source

Use **LLMQuant Data** as the input data source for ETF identity, profile metadata, holdings, weights, sectors, countries, as-of dates, and coverage notices. State which LLMQuant Data capabilities were used and do not invent data that was not retrieved.

---

## LLMQuant Data Contract

Required data capabilities:
- ETF identity and profile lookup
- ETF holdings data

Optional data capabilities:
- equity price history

Freshness:
- Report the holdings as-of date and stale flag.
- Explain that holdings are latest available SEC N-PORT regulatory snapshots, not necessarily current daily issuer holdings.
- Use CUSIP / ISIN when tickers are missing or ambiguous.

Fallback:
- If an ETF is unsupported, report the coverage notice and do not estimate holdings.
- If holdings are partial, compute overlap only on retrieved rows and state the limitation.

Output:
- ETF profile summary
- Top holdings
- Overlap table
- Concentration and exposure notes
- Data used

---

## Workflow

1. Normalize ETF tickers.
2. Query ETF identity and fund profile metadata for each ETF.
3. Query ETF holdings for each ETF with enough rows for the requested comparison.
4. Match holdings by ticker when reliable, otherwise by CUSIP / ISIN.
5. Compute shared names, combined weight, top-name concentration, and sector/country skew from retrieved rows.
6. Report unsupported, partial, or stale coverage clearly.

---

## Output Format

Use:

1. **Bottom Line**
2. **ETF Profiles**: fund name, issuer, category, expense ratio if returned, as-of date.
3. **Overlap Summary**: shared holdings count, overlapping weight, largest common positions.
4. **Top Holdings Table**
5. **Concentration / Exposure Risks**
6. **Coverage Caveats**
7. **Data Used**

---

## Guardrails

- Do not imply N-PORT holdings are live daily holdings.
- Do not estimate missing holdings from memory.
- Do not merge different securities only because names look similar.
- Do not ignore unsupported or stale coverage notices.
