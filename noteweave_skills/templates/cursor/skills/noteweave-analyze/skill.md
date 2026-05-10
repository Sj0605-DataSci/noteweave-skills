---
name: noteweave-analyze
description: Download a paper PDF and run deep E3 analysis on it. Use when the user asks to read a paper, analyze a paper, review a paper, get a critique, summarize methodology, or run deep analysis on research. Also use for batch analysis of multiple papers.
---

# Noteweave Paper Analysis

## Auth
Every request needs: `Authorization: Bearer $NOTEWEAVE_TOKEN`

Get your token: https://apps.noteweave.io/dashboard/tokens → "Generate Token"

Base URL: `https://api.noteweave.io`

---

## Cache check (read first)

Before calling, check whether the answer already exists on disk:

- **Paper PDF / text**: if `.noteweave/papers/<slug>/paper.pdf` or `paper.txt` exists, read it instead of re-downloading or re-fetching.
- **Analysis**: if `.noteweave/papers/<slug>/analysis.md` exists, read it instead of re-running `deep_analyze_paper`.
- **Index lookup**: consult `.noteweave/papers/_index.json` to resolve user-mentioned titles to existing slugs.

Only call the live API when cache is missing or stale.

---

## How papers land in your workspace

Two separate tools — use both together:

| Tool | What it does | Output |
|---|---|---|
| `download_paper` | Streams the actual **PDF binary** to your machine | `.noteweave/papers/<slug>/paper.pdf` |
| `fetch_paper_pdf` | Extracts full **text** from the PDF server-side | `.noteweave/papers/<slug>/paper.txt` |

---

## Tool 1 — download_paper

**GET** `/research/download_paper`

Streams the actual PDF binary to your machine. Use `curl -OJ` — it auto-saves
with the correct filename. Handles large papers (34 MB+).

### Query params (provide at least one)
- `arxiv_id` — e.g. `<arxiv id>`
- `doi` — e.g. `<doi string>`
- `pdf_url` — direct PDF URL
- `title` — paper title (fuzzy matched)
- `url` — landing page URL

### Example
```bash
SLUG="<arxiv id, e.g. arxiv-1706.03762>"
mkdir -p .noteweave/papers/$SLUG

cd .noteweave/papers/$SLUG && curl -OJ \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  "https://api.noteweave.io/research/download_paper?arxiv_id=<arxiv id>" && cd -
```

---

## Tool 2 — fetch_paper_pdf

**POST** `/research/fetch_paper_pdf`

Fetches and extracts full paper text server-side. Large PDFs (100+ MB) are handled.
Cached server-side — repeat calls for the same paper are instant.

### Request body (provide at least one identifier)
```json
{
  "arxiv_id": "<arxiv id>",
  "doi": "<doi string>",
  "pdf_url": "<direct PDF URL>",
  "title": "<exact paper title from search_papers result>",
  "url": "<landing page URL>"
}
```

### Response
```json
{
  "title": "string",
  "text": "string — full extracted paper text (pass to deep_analyze_paper)",
  "arxiv_id": "string or null",
  "doi": "string or null",
  "pdf_url": "string or null",
  "cached": true,
  "chars": 45000
}
```

---

## Tool 3 — deep_analyze_paper

**POST** `/research/deep_analyze_paper`

Run Noteweave's E3 two-pass critic. Uses a domain-expert reviewer persona (ML
reviewer for AI papers, biologist for biology, clinician for medicine).

### Request body
```json
{
  "text": "string (required, min 100 chars) — full paper text from fetch_paper_pdf",
  "title": "<exact paper title from search_papers result>",
  "domain": "auto",
  "pill": "<domain pill, e.g. artificial_intelligence>"
}
```

### Response
```json
{
  "title": "string",
  "review": "string — full structured markdown review",
  "domain": "string",
  "pill": "string"
}
```

### End-to-end example — fetch + analyze + save
```bash
SLUG="<arxiv id, e.g. arxiv-1706.03762>"
TITLE="<exact paper title from search_papers result>"
mkdir -p .noteweave/papers/$SLUG

# Step 1: fetch text → save locally
curl -s -X POST https://api.noteweave.io/research/fetch_paper_pdf \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"arxiv_id\": \"$SLUG\", \"title\": \"$TITLE\"}" \
  | jq -r '.text' > .noteweave/papers/$SLUG/paper.txt

# Step 2: analyze from saved text → save review
curl -s -X POST https://api.noteweave.io/research/deep_analyze_paper \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": $(cat .noteweave/papers/$SLUG/paper.txt | jq -Rs .),
    \"title\": \"$TITLE\",
    \"pill\": \"<domain pill — see noteweave-search for full list>\"
  }" \
  | jq -r '.review' > .noteweave/papers/$SLUG/analysis.md
```

---

## Tool 4 — deep_analyze_batch

**POST** `/research/deep_analyze_batch`

Analyze up to 10 papers concurrently. Much faster than sequential calls.
Save each review to `.noteweave/papers/<slug>/analysis.md` after the call.

### Request body
```json
{
  "papers": [
    {
      "title": "<exact paper title>",
      "text": "string (required, min 100 chars) — contents of paper.txt",
      "pill": "<domain pill>",
      "domain": "auto"
    }
  ]
}
```

### Response
```json
{
  "results": [
    {
      "title": "string",
      "review": "string — full markdown review",
      "error": "string or null"
    }
  ],
  "total": 3
}
```

---

## Persistence

After `download_paper`: save to `.noteweave/papers/<slug>/paper.pdf`.

After `fetch_paper_pdf`:
1. Save extracted text to `.noteweave/papers/<slug>/paper.txt`.
2. Write `.noteweave/papers/<slug>/metadata.json` with the response's `title`, `arxiv_id`, `doi`, `pdf_url`, `chars`, plus `added_at` (ISO timestamp).
3. Update `.noteweave/papers/_index.json` to add this slug.

After `deep_analyze_paper`:
1. Save the review to `.noteweave/papers/<slug>/analysis.md`.
2. Update the slug's entry in `.noteweave/papers/_index.json` with `{analyzed_at: <ISO timestamp>}`.

After `deep_analyze_batch`: same as `deep_analyze_paper`, applied per-paper in the response.

This means future runs can answer "what do I have on <topic>" by reading `.noteweave/papers/_index.json` instead of re-searching.

---

## Rate limits (per user)
| Endpoint | Per minute | Per hour |
|---|---|---|
| fetch_paper_pdf | 10 | 100 |
| deep_analyze_paper | 5 | 50 |
| deep_analyze_batch | 2 | 20 |

HTTP 429 → rate limited, check `Retry-After` header.
HTTP 402 → token quota exhausted, upgrade at https://apps.noteweave.io/dashboard/billing
HTTP 504 → job timed out (heavy analysis), retry once.
