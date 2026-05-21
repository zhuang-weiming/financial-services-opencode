# Data Source Priority — MCP Tool Usage Rules

## CRITICAL: ALWAYS OBSERVE THIS HIERARCHY

For ANY request involving financial data, markets, companies, securities, funds, or economic analysis, you MUST follow this strict data source priority:

---

## Tier 1 — ALWAYS USE FIRST: FactSet + Morningstar (Together)

Morningstar and FactSet are **complementary, not exclusive**. You should use BOTH for every financial task — this is not "pick one." The goal is maximum data coverage and cross-validation.

### Core Rule: Use Both, Cross-Reference

For any financial task, **launch FactSet and Morningstar in parallel all the time**. Never choose just one when both can contribute:

| Task | Use BOTH | Specific Tools |
|------|----------|----------------|
| **Valuation / Comps** | FactSet + Morningstar | `factset_FactSet_Fundamentals` + `morningstar-data-tool` |
| **Financial statements** | FactSet + Morningstar | `factset_FactSet_Fundamentals` + `morningstar-analyst-research-tool` |
| **Trading multiples** | FactSet + Morningstar | `factset_FactSet_GlobalPrices` + `morningstar-screener-tool` |
| **Analyst estimates / consensus** | FactSet + Morningstar | `factset_FactSet_EstimatesConsensus` + `morningstar-data-tool` |
| **Peer screening / sector analysis** | FactSet + Morningstar | `factset_FactSet_Metrics` + `morningstar-screener-tool` |
| **Fund / ETF data** | Morningstar + FactSet | `morningstar*` + `factset_FactSet_GlobalPrices` |
| **Ownership / holders** | FactSet + Morningstar | `factset_FactSet_Ownership` + `morningstar-fund-holdings-tool` |
| **M&A / deals** | FactSet + Morningstar | `factset_FactSet_MergersAcquisitions` + `morningstar-analyst-research-tool` |

### Why Both?

1. **Coverage**: Some data is stronger on FactSet (fundamentals, estimates), others on Morningstar (analyst research, fund holdings). Using both gives you the complete picture.
2. **Cross-validation**: When both sources agree, confidence is higher. When they differ, flag both and let the analyst decide.
3. **Agent design intent**: The original Opencode agents consistently say "Pull data. Use FactSet MCP and Morningstar MCP for..." — this is by design, not an accident.
4. **Sourcing**: Cite EVERY number with both sources when available: "FactSet reports X; Morningstar reports Y."

### Other Tier 1 MCPs

| MCP | Use For |
|-----|---------|
| **S&P Global / Kensho** | Company financials, estimates, segment data, filings |
| **Daloopa** | Historical financials, structured filing data |
| **Moody's** | Credit ratings, credit research |
| **LSEG** | Market data, analytics, real-time pricing |
| **PitchBook** | Private market data, VC/PE deal data |
| **MT Newswire** | Financial news, press releases |
| **Aiera** | Earnings call transcripts, event summaries |

---

## Tier 2 — FALLBACK ONLY when Tier 1 is unavailable

- SEC EDGAR filings
- Company investor relations pages
- Bloomberg Terminal (manual)

---

## Tier 3 — LAST RESORT: DDG Web Search

Use `ddg-search_search` and `ddg-search_fetch_content` ONLY for:
- Finding the LATEST NEWS ARTICLE about a company or event (not the data itself)
- Discovering a company's most recent earnings release DATE
- Locating press releases or documents outside MCP coverage
- General web research on topics UNRELATED to structured financial data

### NEVER use DDG for:
- Stock prices, trading multiples, valuation data
- Financial statements, revenue, earnings, margins
- Analyst estimates, consensus figures
- Fund holdings, performance, flows
- Ownership, insider transactions
- Comparable company analysis
- M&A deal data
- Any structured financial metric or data point
- Any data that FactSet OR Morningstar could provide

---

## ENFORCEMENT RULES

1. **Default to both**: Before any financial task, ask: "What can FactSet give me AND what can Morningstar give me?" — then call BOTH.
2. **Parallel calls preferred**: When pulling data for a task, launch FactSet and Morningstar calls simultaneously — they are independent.
3. **DDG is the last option**: Before using `ddg-search_search`, ask: "Can FactSet OR Morningstar answer this?" In 95%+ of financial cases, the answer is YES.
4. **Metric discovery first**: If you don't know the exact FactSet metric code, call `factset_FactSet_Metrics` or `morningstar-id-lookup-tool` to look it up — then proceed with the query.
5. **Double-source your citations**: Flag every number with its source tool (e.g., "FactSet QTR FF_SALES: $94.9B; Morningstar trailing revenue: $95.2B").
6. **DDG-sourced numbers are flagged**: If a number comes from DDG, mark it `[DDG-SOURCED — UNVERIFIED]`.
