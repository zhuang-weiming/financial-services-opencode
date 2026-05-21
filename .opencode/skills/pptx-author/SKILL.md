---
name: pptx-author
description: Produce a .pptx file on disk (headless) or display content directly (Opencode Web) — for managed-agent sessions with no open Office app or when outputting presentation content to the chat interface.
---

# pptx-author

Use this skill when you need to deliver a PowerPoint presentation — either as a file artifact (headless/CMA mode) or as formatted content displayed directly in the Opencode Web chat interface.

## Environment Detection

**Check which environment you're in before deciding output format:**

- **Opencode Web / Chat Interface**: Display content directly in chat with proper markdown formatting. Structure the output as a presentation outline with slide-by-slide content. Do NOT write to disk.
- **Headless / Managed-agent (CMA)**: Write to `./<name>.pptx` and return the path.

When in doubt, prefer **displaying content directly** in chat — this is the default for Opencode Web.

## Output Contract

### For Opencode Web (default)
- Display content directly in chat using markdown formatting
- Structure output as a presentation outline with clear slide hierarchy
- Use headings (## Slide 1: Title), tables for data, and bullet points for content
- Return structured, well-formatted content that the user can read immediately

### For Headless (CMA mode)
- Write to `./<name>.pptx`
- Return the relative path in your final message so the orchestration layer can collect it

## Output Content Structure

### For Opencode Web Presentation Output

Structure each slide as follows:

```
## Slide 1: [Slide Title]

**[Takeaway Statement]**

| Element | Content |
|--------|---------|
| Company/Topic | [Name] |
| Metric | [Value] |
| Source | [Source reference] |

**Key Points:**
- [Bullet 1]
- [Bullet 2]
- [Bullet 3]

---

## Slide 2: [Slide Title]

... continue with same structure ...
```

### For Headless (CMA mode) — How to Build the Deck

Write a short Python script and run it with Bash. Use `python-pptx`:

```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation("./templates/firm-template.pptx")  # if a template is provided
# or: prs = Presentation()

slide = prs.slides.add_slide(prs.slide_layouts[5])    # title-only
slide.shapes.title.text = "Valuation Summary"
# ... add tables / charts / text boxes ...

prs.save("./pitch-<target>.pptx")
```

## Conventions (mirror the live-Office `pitch-deck` skill)

- **One idea per slide.** Title states the takeaway; body supports it.
- **Every number traces to the model.** If a figure comes from a data source, include the source reference.
- **Use the firm template** when one is mounted at `./templates/`; otherwise default layouts.
- **Charts**: prefer embedding a description of the chart rather than trying to embed images unless the environment supports it.
- **No external sends.** This skill produces content; it never emails or uploads.

## When NOT to use

If `mcp__office__powerpoint_*` tools are available (Cowork plugin mode), use those instead — they drive the user's live document with review checkpoints. This skill is the file-producing fallback for headless runs, or content display for Opencode Web.
