# HSBC PPT Style Guide

> Derived from `out/Wealth-Guide-Jam.pptx` (Jam Competition deck, July 2026)
> Applies to all future HSBC-facing PowerPoint deliverables

## Colors — White / Red / Gray Only

| Token | Hex | Usage |
|-------|-----|-------|
| HSBC Red | `#DB001C` | Titles, section headers, accent bars, red-box items, bottom taglines |
| White | `#FFFFFF` | Slide backgrounds, card fills, text on red backgrounds |
| Light Gray | `#F2F2F2` | Card backgrounds for left panels, demo cards |
| Divider Gray | `#E8E8E8` | Thin horizontal divider lines between sections |
| Dark Gray | `#333333` | All body and header text on white/light backgrounds |
| Medium Gray | `#888888` | Secondary/description text (e.g. "what Wealth-Guide does" answers) |

No navy, no blue, no other brand colors.

## Slide Dimensions

- **Widescreen 16:9** — 13.333 x 7.5 inches

## Typography

| Role | Size | Weight | Color |
|------|------|--------|-------|
| Slide title | 38 pt | Bold | HSBC Red |
| Subtitle | 16 pt | Regular | Dark Gray |
| Section header (panel title) | 17 pt | Bold | HSBC Red |
| Sub-header (within section) | 13 pt | Bold | Dark Gray |
| Body text | 11 pt | Regular | Dark Gray |
| Bullet / list items | 10 pt | Regular | Dark Gray |
| Item title (right panel) | 11 pt | Bold | Dark Gray |
| Scenario question text | 9 pt | Regular | Dark Gray |
| Scenario answer text | 8 pt | Regular | Medium Gray |
| Architecture box text | 9 pt | Bold | White or Dark Gray |
| Demo card title | 12 pt | Bold | HSBC Red |
| Bottom tagline | 11 pt | Bold | HSBC Red |

Font: Calibri (implied). Do not use other fonts.

## Layout Rules

### Slide Structure (top to bottom)
1. **Red top bar** — thin rectangle spanning full width, ~6 pt tall (at y=0)
2. **Title** — position (0.60, 0.10), width 11"
3. **Subtitle** — position (0.60, 0.85), width 11"
4. **Thin gray divider line** — at y≈1.35, width 12.1" (for content slides)
5. **Content panels** — two-column or single-column layout
6. **Bottom tagline** — centered, at y≈7.1 (slide bottom)

### Two-Column Panel Layout
- **Left panel card:** (0.50, 1.39), size 6.00 x 5.60, Light Gray fill
- **Right panel card:** (6.90, 1.39), size 6.00 x 5.60, White fill, **red left border** (thin rectangle at x=6.90, same height)

### Architecture Flow Boxes
- Horizontal row of 6 boxes: 1.90 x 1.00 each, evenly spaced
- White boxes → dark gray text (standard steps)
- Red boxes (fill=#DB001C) → white text (entry/exit: Router, Answer)
- Text centered within box, 9 pt bold

### Demo Cards (3-across)
- Evenly spaced at y≈3.12, size 3.90 x 3.98 each
- Light Gray fill
- Red thin border at top of card
- Internal structure: Title → "Question" label → Question text → "What audience sees" label → Steps

## Shape Conventions

| Element | Shape Type | Notes |
|---------|-----------|-------|
| Cards | ROUNDED_RECTANGLE | No stroke, no shadow |
| Accent bars | RECTANGLE | Thin, solid fill |
| Dividers | RECTANGLE | Very thin (0 pt height), gray fill |
| Architecture boxes | ROUNDED_RECTANGLE or RECTANGLE | White or Red fill |

## Text Conventions

- **No abbreviations** — spell out "Relationship Manager" not "RM",
  "Strategic Asset Allocation" not "SAA", "Global Investment Research" not "GIR"
- **Plain language** — avoid jargon. Use "artificial intelligence" not "AI" in first mention
- **Concrete scenarios** — each capability point has: exact question the RM asks (in quotes) + what the system does (in plain language)
- **Customer-centric framing** — talk about what the RM does for the customer, not what the system does internally
- **Bottom tagline** — every content slide ends with a one-line tagline in Red, centered, 11 pt bold
