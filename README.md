# Opencode for Financial Services

Reference agents, skills, and data connectors for the financial-services workflows we see most — investment banking, equity research, private equity, and wealth management.

## Agents & Ask Questions

### Earnings Reviewer
Processes an earnings event end to end — reads the call transcript and filings, updates the coverage model, and drafts the post-earnings note.

**Ask questions:**
1. "AAPL just reported Q3 2025 earnings. Pull the actuals from FactSet, update my coverage model, and draft the post-earnings note with a variance table vs. consensus. Show me the updated estimates and the variance table directly."
2. "Run the full earnings review for MSFT after their Q2 print — transcript, model update, and note. Flag any guidance changes vs. prior quarter and show me the key takeaways."
3. "I need a variance table for TSLA Q1 2025: actual vs. consensus vs. my prior estimate for revenue, gross margin, EBITDA, and EPS. Display it as a formatted table."
4. "Review NVDA's latest earnings call transcript and tell me which questions management dodged. Summarize the new guidance and how it impacts my estimates."
5. "Fan out the earnings review across my coverage list (AAPL, MSFT, GOOGL, AMZN, META) for this reporting season. Show me a summary table of beats/misses and estimate changes for each name."

### Equity Research
Produces institutional equity research — initiating coverage reports, earnings notes, sector primers, and model updates.

**Ask questions:**
1. "Write an initiating coverage report on SNOW. Include business overview, industry context, competitive positioning, DCF + comps valuation, investment thesis, and risks. Show me the full report."
2. "Draft an earnings update note for CRM after their Q4 print — headline read, variance vs. consensus, estimate changes, and updated price target. Display the variance table inline."
3. "Build a sector primer on the US cybersecurity industry: market size, value chain, competitive landscape, comps spread, and 3-5 investment ideas. Show me the comps table and the ideas shortlist."
4. "Update my coverage model for ADBE with the latest actuals and roll forward estimates. Flag any variances vs. consensus and show me the updated estimates table."
5. "Produce a sector primer on the EV battery supply chain — identify 8-15 names, spread the comps, and shortlist the top 3 names with thesis hooks. Display the comps table and shortlist."

### Financial Analysis
Builds institutional-quality financial models — DCF, LBO, trading comps, and integrated three-statement models.

**Ask questions:**
1. "Build a DCF model for COST: 10-year projection, WACC build via CAPM, terminal value, and sensitivity tables on WACC × terminal growth and WACC × exit multiple. Show me the valuation summary and sensitivity table."
2. "Create an LBO model for a take-private of DELL at 8x EBITDA entry. Include sources & uses, debt schedule, returns waterfall, and IRR/MOIC sensitivities. Display the returns summary."
3. "Build a fully integrated three-statement model for UBER with working capital schedules, debt schedules, and balance checks on every period. Show me the key financial projections and balance checks."
4. "Spread trading comps for the fintech peer set (SQ, AFRM, SOFI, UPST, FOUR) — show max, 75th, median, 25th, min with outlier flags. Display as a formatted comps table."
5. "Build a DCF for AMZN with three scenarios (bull/base/bear). Show me the valuation range and key assumptions for each scenario in a comparison table."

### GL Reconciler
Reconciles general ledger to subledger across asset classes for a trade date — finds breaks, traces root cause, and routes the exception report.

**Ask questions:**
1. "Run the GL ↔ subledger reconciliation for trade date 2025-06-15 across all asset classes. Show me every break over $10K with suspected cause in a table."
2. "Trace the root cause of the $50K variance in fixed income from yesterday's recon. Is it timing, system drift, or a reclass? Show me the transaction-level evidence."
3. "Generate the exception report for today's recon run — show me the break list with account, balances, variance, and recommended resolution for each."
4. "Re-run the equity reconciliation for last week. I want to see all breaks that were resolved vs. still open — show me a status table."
5. "Compare GL and subledger balances for derivatives only — trade date 2025-06-14. Flag any variances over $5K and display the comparison table."

### Investment Banking
Produces investment banking execution materials — CIMs, teasers, one-pagers, merger models, and process letters.

**Ask questions:**
1. "Draft a CIM for a confidential sell-side process on a mid-market SaaS company. Include business overview, industry overview, financial summary, and growth strategy. Show me the full document."
2. "Build a merger consequences model for a potential acquisition of WBD by CMCSA — accretion/dilution, pro-forma financials, sources & uses, and EPS sensitivity. Display the accretion/dilution table."
3. "Create a blind teaser for a healthcare services company we're taking to market. Keep it anonymous with key selling points and financial highlights. Show me the teaser."
4. "Generate a buyer list for a specialty chemicals company — identify 10-15 strategic acquirers and financial sponsors with rationale per buyer. Display as a structured table."
5. "Draft a process letter for the second-round (final bid) stage of an auction for a consumer goods company. Include bid instructions and data room access. Show me the letter."

### KYC Screener
Parses an onboarding document packet, runs KYC/AML rules, screens against sanctions and PEP lists, and flags gaps for escalation.

**Ask questions:**
1. "Process the onboarding packet for a new corporate client — extract entity details, beneficial owners, and run the full KYC/AML rules engine. Show me the extracted entity file and rules results."
2. "Screen the following entity against sanctions, PEP, and adverse media lists: 'ABC Holdings Ltd', registered in the Cayman Islands. Show me the screening results with match confidence."
3. "Run the KYC rules on this onboarding file and flag every rule that fails. Include the evidence reference for each failure — display as a pass/fail table."
4. "Generate the escalation packet for a high-risk client onboarding — include all gaps, hits, and a recommended risk rating for compliance sign-off. Show me the summary."
5. "Perform a periodic KYC refresh on client ID 4421 — re-screen all beneficial owners and update the risk rating recommendation. Display the screening results."

### Market Researcher
Produces sector or thematic market research — industry overview, competitive landscape, trading-comps spread, and a thematic ideas shortlist.

**Ask questions:**
1. "Write a sector primer on the AI semiconductor space — market size, value chain, key players, and 3-5 investment ideas with thesis hooks. Show me the full primer."
2. "Research the carbon capture theme: map the competitive landscape, spread comps for 8-15 names, and shortlist the best ways to play it. Display the comps table and shortlist."
3. "Build a research note on the US renewable energy sector — include market growth drivers, regulatory landscape, and a comps spread of the peer set. Show me the note."
4. "Analyze the digital payments theme: who are the key players, what's their market positioning, and which 3 names best express the theme? Display the competitive landscape."
5. "Produce a sector overview on enterprise software — structure, key trends, comps analysis, and a shortlist of names with one-line thesis hooks. Show me the comps table and ideas."

### Meeting Prep Agent
Builds a briefing pack before a client or prospect meeting — relationship history, holdings, market context, and a suggested agenda.

**Ask questions:**
1. "Build a briefing pack for my 2 PM meeting with client Acme Corp — pull relationship history, holdings snapshot, and recent activity. Show me the full briefing."
2. "Prepare talking points for a prospect meeting with a large family office — include their known holdings, recent market events affecting their portfolio, and 3-5 items I should raise. Display the talking points."
3. "I have a meeting with client ID 8832 tomorrow at 10 AM. Generate the full briefing pack with relationship summary and suggested agenda. Show me everything."
4. "Pull the latest market context relevant to client XYZ's portfolio — any earnings or macro events this week that touch their holdings. Display the relevant events."
5. "Draft a one-page prep memo for my quarterly review with the Johnson Foundation — holdings performance, open items, and discussion agenda. Show me the memo."

### Model Builder
Builds DCF, LBO, three-statement, and trading-comps models live from a ticker and assumption set.

**Ask questions:**
1. "Build a DCF model for META from scratch — 10-year projection, WACC, terminal value, and sensitivity tables. Use FactSet for inputs. Show me the valuation summary and sensitivity table."
2. "Create an LBO model for a potential take-private of ROKU at 7x EBITDA. Include sources & uses, debt schedule, and IRR/MOIC sensitivities. Display the returns summary."
3. "Build a three-statement model for SHOP with integrated IS/BS/CF, working capital schedules, and balance checks on every period. Show me the key projections."
4. "Spread trading comps for the cloud computing peer set (AMZN, MSFT, GOOGL, CRM, NOW) — show summary statistics and flag outliers. Display as a formatted comps table."
5. "Build a DCF for TSLA with a 5-year projection period and sensitivity on WACC (8-12%) vs. terminal growth (2-5%). Show me the valuation range table."

### Month-End Closer
Runs the month-end close for an entity — accruals, roll-forwards, and variance commentary — and stages the close package.

**Ask questions:**
1. "Run the month-end close for entity 'Global Equity Fund' for June 2025 — build the accrual schedule, roll-forwards, and variance commentary. Show me the close summary."
2. "Draft the accrual schedule for this month's close — each entry needs the calculation, support reference, and a JE draft. Display as a table."
3. "Generate variance commentary for the P&L — flux every line over 10% vs. prior period and budget, with explanations from underlying activity. Show me the variance table."
4. "Build roll-forward schedules for all balance sheet accounts — beginning balance + activity − reversals = ending, tied to the GL. Display the roll-forward table."
5. "Assemble the full close package for May 2025 — show me the accrual schedule, roll-forwards, and variance commentary formatted for controller review."

### Pitch Agent
End-to-end investment banking pitch agent — pulls comps and precedents, builds valuation, and generates a pitch deck.

**Ask questions:**
1. "Build a full pitch for a potential mandate advising on the sale of a mid-market SaaS company — comps, precedents, DCF, football field. Show me the valuation summary and football field table."
2. "Generate a pitch for a SPAC merger advisory mandate — include situation overview, valuation summary, comps detail, and illustrative process timeline. Show me the pitch content."
3. "Build the valuation analysis for a pitch to a PE firm looking at acquiring a healthcare services platform — comps, LBO, DCF, and football field. Display the valuation ranges."
4. "Create a first-draft pitch for a cross-border M&A advisory mandate — target is a European luxury goods company, buyer is a US strategic. Show me the situation overview and valuation."
5. "Run QC on the pitch materials for the Acme Corp mandate — verify totals tie, footnotes present, dates consistent. Show me the QC checklist results."

### Statement Auditor
Audits a batch of pre-generated LP capital-account statements against the fund NAV pack before distribution.

**Ask questions:**
1. "Audit the Q2 2025 LP statement batch against the fund NAV pack — produce a tie-out table showing match/mismatch for every field. Display the results."
2. "Run the final check on the June LP statements before they go out — flag every discrepancy with suspected cause. Show me the exception list."
3. "Generate the sign-off sheet for the latest statement batch — pass/hold recommendation per LP statement. Display as a table."
4. "Reconcile the capital-account statements for Fund III against the NAV pack — focus on allocations and fee calculations. Show me the reconciliation."
5. "Audit the batch of 50 LP statements and give me a summary: how many pass, how many have exceptions, and what are the top 3 most common discrepancies? Display the summary."

### Valuation Reviewer
Ingests GP valuation packages for a fund, runs them through the valuation template, and stages LP reporting.

**Ask questions:**
1. "Review the Q2 2025 GP valuation packages for Fund IV — produce a valuation summary per portfolio company with methodology, key inputs, and reviewer flags. Display the summary table."
2. "Run the waterfall for the fund — compute fund-level NAV, carried interest, and LP allocations as of June 30, 2025. Show me the waterfall table."
3. "Stage the LP reporting pack for Q2 2025 — show me the valuation summary and waterfall formatted for IR review."
4. "Review the valuation of portfolio company PortCo-12 — compare the GP's reported mark to our valuation policy and flag any discrepancies. Show me the review."
5. "Ingest all GP packages for the calendar year-end and run the full valuation template — highlight any companies where the valuation methodology changed vs. prior quarter. Display the comparison."
