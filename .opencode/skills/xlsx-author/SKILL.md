---
name: xlsx-author
description: Produce a .xlsx file on disk (headless) or display content directly (Opencode Web) — for managed-agent sessions with no open Office app or when outputting content to the chat interface.
---

# xlsx-author

Use this skill when you need to deliver an Excel workbook — either as a file artifact (headless/CMA mode) or as formatted content displayed directly in the Opencode Web chat interface.

## Environment Detection

**Check which environment you're in before deciding output format:**

- **Opencode Web / Chat Interface**: Display content directly in chat with proper formatting (markdown tables, structured text). Do NOT write to disk.
- **Headless / Managed-agent (CMA)**: Write to `./<name>.xlsx` and return the path.

When in doubt, prefer **displaying content directly** in chat — this is the default for Opencode Web.

## Output Contract

### For Opencode Web (default)
- Display content directly in chat using markdown formatting
- Use tables for tabular data, code blocks for structured output
- Return structured, well-formatted content that the user can read immediately
- No file write needed — just output the content with clear structure

### For Headless (CMA mode)
- Write to `./<name>.xlsx`
- Return the relative path in your final message so the orchestration layer can collect it

## How to Build the Workbook (Headless only)

Write a short Python script and run it with Bash. Use `openpyxl`:

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

wb = Workbook()
ws = wb.active; ws.title = "Inputs"
ws["B2"] = "Revenue"; ws["C2"] = 1_250_000_000
ws["C2"].font = Font(color="0000FF")           # blue = hardcoded input
calc = wb.create_sheet("DCF")
calc["C5"] = "=Inputs!C2*(1+Inputs!C3)"        # black = formula
wb.save("./model.xlsx")
```

## Output Content Structure

### For Tabular Data (Table Format)
When outputting structured data in Opencode Web, use markdown tables:

```
| Metric | Value | Unit |
|--------|-------|------|
| Revenue | 1,250 | $M |
| EBITDA | 340 | $M |
| Margin | 27.2% | % |
```

### For Model Structure
When outputting financial model content:

```
## Inputs Sheet
| Cell | Label | Value |
|------|-------|-------|
| B2 | Revenue | 1,250 |
| B3 | Growth Rate | 5.0% |

## DCF Sheet
| Cell | Formula | Result |
|------|---------|--------|
| C5 | =Inputs!C2*(1+Inputs!C3) | 1,312.5 |
```

## Conventions (mirror `audit-xls`)

- **Blue / black / green.** Blue = hardcoded input, black = formula, green = link to another sheet/file.
- **No hardcodes in calc cells.** Every calculation cell is a formula; every input lives on an Inputs tab.
- **Named ranges** for any value referenced from a deck or memo.
- **Balance checks.** Include a Checks tab that ties (BS balances, CF ties to cash, etc.) and surfaces TRUE/FALSE.
- **One model per file.** Do not append to an existing workbook unless explicitly asked.

## When NOT to use

If `mcp__office__excel_*` tools are available (Cowork plugin mode), use those instead — they drive the user's live workbook with review checkpoints. This skill is the file-producing fallback for headless runs, or content display for Opencode Web.
