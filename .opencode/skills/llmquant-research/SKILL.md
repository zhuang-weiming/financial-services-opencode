---
name: llmquant-research
description: Knowledge bases for finance methodology — arxiv papers (English, structured by section) and a zh-leaning finance concept wiki. Use for "find a paper on X", "what's the canonical reference for Y", "explain concept Z", or any methodology citation request.
category: data-source
---

# llmquant-research

Two complementary knowledge bases:

1. **Papers** — arxiv-style academic papers with section-level extraction (introduction, methodology, experiments, references, etc.)
2. **Wiki** — finance concept wiki, zh-leaning, with bilingual coverage of fundamental concepts (Sharpe ratio, CAPM, M&A, factor investing, etc.)

Four tools, all read-only.

> Pair with `llmquant-data` master for cross-cutting concerns. This skill is tool-by-tool usage.

## When to use

- "Find the canonical paper on Sharpe ratio" → `paper_search`
- "Read the methodology section of paper X" → `paper_read(sections=["methodology"])"
- "Explain risk parity in Chinese" → `wiki_search` (zh-friendly)
- "What is a CAPM?" → `wiki_read`

## When NOT to use

- **Live market commentary** → `llmquant-news` or web search
- **Working papers / NBER / SSRN** → not indexed; use Semantic Scholar / arxiv search
- **Wikipedia in general** → use DDG search; this is a curated finance wiki only
- **Books** → some titles are listed but not full-text readable

---

## Papers (arxiv)

### `paper_search`

Semantic search over the paper knowledge base.

| Param | Type | Required | Notes |
|---|---|---|---|
| `query` | string | yes | Natural language, max 2000 chars |
| `limit` | int | no | 1–10, default 5 |

**Returns**: array of `{paperCardId, sourcePaperId (arxiv:NNNN.NNNNN), title, authors, abstract, summary, tags, availableSections[], sectionCount, fullTextCharCount, pdfUrl, semanticScore}`.

```python
paper_search("Sharpe ratio deflated", limit=3)
# → Returns 3 papers w/ semantic score + available sections
```

**Cost**: 1 credit.

**Output fields to surface**: `title`, `authors`, `summary` (LLM-generated digest, ~3-5 sentences), `pdfUrl` (canonical link), `paperCardId` (for follow-up `paper_read`).

### `paper_read`

Read one or more sections of a paper.

| Param | Type | Required | Notes |
|---|---|---|---|
| `paperCardId` | string (UUID) | yes | From `paper_search` |
| `sections` | string[] | no | Section keys from `paper_search.availableSections`. `["all"]` or omit = load everything |

**Returns**: paper metadata + the requested sections' `bodyMarkdown`. Each section has `{paperCardId, sectionKey, sectionType, title, sectionOrder, bodyMarkdown, charCount}`.

```python
# Load methodology + experiments only — most useful for a research workflow
paper_read(paperCardId="591ac848-...", sections=["methodology", "experiments"])

# Full paper (large!)
paper_read(paperCardId="591ac848-...")  # ~38 KB for a typical paper
```

**Cost**: 0 credits per section (but sections are large; multi-section reads can be 50-200 KB).

**Section key conventions** (per the response's `availableSections`):

| SectionKey | Typical content |
|---|---|
| `introduction` | Problem statement, contributions |
| `related_work` | Literature review |
| `methodology` | Model / approach / derivation |
| `experiments` | Empirical setup + results |
| `results` | Quantitative findings |
| `discussion` | Interpretation |
| `conclusion` | Summary + future work |
| `references` | Bibliography |
| `appendix` | Supporting derivations / extra figures |

## Patterns

### "Read the methodology of paper X"

```python
results = paper_search("direct reinforcement learning portfolio", limit=5)
top = results[0]  # pick the most relevant
paper_read(paperCardId=top["paperCardId"], sections=["methodology", "experiments"])
```

### Citation

```python
results = paper_search("deflated Sharpe ratio", limit=1)
p = results[0]
print(f"{', '.join(p['authors'])} ({p['sourcePaperId']}). {p['title']}.")
# → Bailey, D. & López de Prado, M. (arxiv:1407.XXXX). The Deflated Sharpe Ratio.
```

### Background reading for a strategy

```python
# Find papers on low-volatility anomaly
papers = paper_search("low volatility anomaly factor", limit=5)
for p in papers:
    abstract = paper_read(p["paperCardId"], sections=["introduction"])
    # decide which papers to deep-read
```

## Coverage flags

- `paper_search` returns `semanticScore` (0-1). Use ≥0.3 as a "high relevance" cut-off
- `fullTextCharCount` indicates paper completeness — smaller numbers may mean the paper was only partially indexed
- `pdfUrl` always points to arxiv.org (canonical) for verification

## See also

- `sec-edgar` (skill) — for SEC filings, not academic papers
- Web search (DDG) — for non-arxiv papers / NBER / SSRN

---

## Wiki (zh-leaning concept wiki)

### `wiki_search`

Keyword + semantic search over the concept wiki.

| Param | Type | Required | Notes |
|---|---|---|---|
| `query` | string | yes | Natural language or Chinese keyword, max 2000 chars |
| `limit` | int | no | 1–10, default 5 |

**Returns**: array of `{wikiItemId, slug, title, summary, tags[], semanticScore, lexicalScore, combinedScore}`.

```python
wiki_search("risk parity portfolio", limit=3)
# → 3 hits, mixed zh/en, sorted by combinedScore

wiki_search("夏普比率", limit=3)
# → Chinese entries score higher on lexicalScore
```

**Cost**: 1 credit.

### `wiki_read`

Load a full wiki entry.

| Param | Type | Required | Notes |
|---|---|---|---|
| `wikiItemId` | string (UUID) | yes | From `wiki_search` |
| `maxLength` | int | no | Preview-only char limit on `bodyMarkdown` |

**Returns**:

```json
{
  "wikiItemId": "...",
  "slug": "start/sharpe",
  "title": "你真的读懂夏普比率？量化交易员带你入门Sharpe Ratio",
  "summary": "本文通俗介绍了夏普比率（Sharpe Ratio）的核心思想...",
  "bodyMarkdown": "...markdown body...",
  "tags": ["finance", "quant", ...],
  "aliases": [],
  "relatedConcepts": [],
  "sourceUpdatedAt": "2026-02-25T...",
  "createdAt": "2026-03-13T...",
  "updatedAt": "2026-03-18T..."
}
```

**Cost**: 0 credits.

**Note**: `bodyMarkdown` is full Chinese with embedded images. Use `maxLength=800` to preview before committing to a full read.

```python
# Find then read
hits = wiki_search("risk parity", limit=3)
entry = wiki_read(wikiItemId=hits[0]["wikiItemId"], maxLength=800)
# Now decide whether to load full body
if "..." in entry["bodyMarkdown"][-50:]:
    entry = wiki_read(wikiItemId=hits[0]["wikiItemId"])
```

## Patterns

### Concept primer for a downstream report

```python
# When asked to write a risk-parity explainer:
hits = wiki_search("风险平价", limit=3)
for h in hits:
    entry = wiki_read(wikiItemId=h["wikiItemId"], maxLength=1500)
    # synthesize entry["summary"] + entry["bodyMarkdown"][:1500] into the report
```

### Bilingual quick reference

```python
# English search → Chinese result (or vice versa)
zh_hits = wiki_search("Sharpe ratio", limit=3)
en_hits = wiki_search("夏普比率", limit=3)
# both return overlapping entries; combined score handles language matching
```

## Coverage flags

- `combinedScore` weights semantic + lexical; pure lexical (Chinese keyword match) and pure semantic both produce usable hits
- `tags` indicate language level (`beginner`, `intermediate`, `advanced`, `concept`, `tutorial`, `reference`)
- Slug prefix tells you the section: `basic/`, `advanced/`, `start/`, `ai/`, `library/`, `FAQ`

## See also

- `paper_search` / `paper_read` — for academic methodology
- Web search (DDG) — for live tutorials, blog posts
- `llmquant-news` — for current events, not concepts

---

## Combined patterns

### "Explain concept X, citing paper Y"

```python
# 1. Wiki primer
wiki = wiki_search("X", limit=3)[0]
primer = wiki_read(wiki["wikiItemId"], maxLength=2000)

# 2. Academic backing
papers = paper_search("X methodology", limit=5)

# 3. Compose: wiki primer + paper citations + 1-2 paragraphs of your own analysis
```

### Bibliography for a research report

```python
# Build a citation list
papers = paper_search("factor model cross-section", limit=10)
bib = []
for p in papers:
    authors = ", ".join(p["authors"][:3])
    bib.append(f"{authors} ({p['sourcePaperId']}). {p['title']}.")
# Use bib in the report's references section
```

## Output size

| Call | Approx size |
|---|---:|
| `paper_search` | < 5 KB |
| `paper_read(sections=['methodology'])` | ~10 KB |
| `paper_read(all)` | ~50-200 KB depending on paper length |
| `wiki_search` | < 3 KB |
| `wiki_read(maxLength=800)` | < 2 KB |
| `wiki_read` (full) | ~10-30 KB |

`paper_read(all)` on long papers can approach the opencode runtime's display truncation threshold — fetch specific sections when possible.