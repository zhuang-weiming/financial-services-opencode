---
name: xlsx-author
description: Display tabular financial model content directly in chat with proper markdown formatting. Use when users need to view DCF models, comps analysis, LBO models, or 3-statement models. Output is formatted markdown tables, NOT Excel files.
---

# xlsx-author

Use this skill when you need to deliver tabular financial model content — formatted as markdown tables displayed directly in the Opencode Web chat interface.

## Environment Detection

**Check which environment you're in before deciding output format:**

- **Opencode Web / Chat Interface**: Display content directly in chat with proper formatting (markdown tables, structured text). Do NOT write to disk.
- **Headless / Managed-agent (CMA)**: Display content directly in chat. Do NOT write to disk.

When in doubt, prefer **displaying content directly** in chat — this is the default for Opencode Web.

## Output Contract

### For Opencode Web and Headless/CMA (default for both)
- Display content directly in chat using markdown formatting
- Use tables for tabular data, code blocks for structured output
- Return structured, well-formatted content that the user can read immediately
- Do NOT write to disk under any circumstances

## Conventions (mirror `audit-xls`)

- **Blue / black / green.** Blue = hardcoded input, black = formula, green = link to another sheet/file.
- **No hardcodes in calc cells.** Every calculation cell is a formula; every input lives on an Inputs tab.
- **Named ranges** for any value referenced from a deck or memo.
- **Balance checks.** Include a Checks tab that ties (BS balances, CF ties to cash, etc.) and surfaces TRUE/FALSE.
- **One model per file.** Do not append to an existing workbook unless explicitly asked.

## When NOT to use

If `mcp__office__excel_*` tools are available (Cowork plugin mode), use those instead — they drive the user's live workbook with review checkpoints. This skill is the file-producing fallback for headless runs, or content display for Opencode Web.
