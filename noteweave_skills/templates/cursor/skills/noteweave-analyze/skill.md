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

## Workflow

```
search_papers  →  fetch_paper_pdf  →  deep_analyze_paper
                                   →  deep_analyze_batch (for multiple papers)
```

---

## Tool 1 — fetch_paper_pdf

**POST** `/research/fetch_paper_pdf`

Download a paper PDF and return its full extracted text. Results are cached server-side — repeat calls for the same paper are instant.

### Request body (provide at least one identifier)
```json
{
  "arxiv_id": "2307.09288",
  "doi": "10.1145/3292500.3330681",
  "pdf_url": "https://arxiv.org/pdf/2307.09288",
  "title": "Attention Is All You Need",
  "url": "https://arxiv.org/abs/2307.09288"
}
```

### Response
```json
{
  "title": "string",
  "text": "string — full extracted paper text",
  "arxiv_id": "string or null",
  "doi": "string or null",
  "pdf_url": "string or null",
  "cached": true,
  "chars": 45000
}
```

### Example
```bash
curl -s -X POST https://api.noteweave.io/research/fetch_paper_pdf \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"arxiv_id": "1706.03762"}' | jq '{title, cached, chars}'
```

---

## Tool 2 — deep_analyze_paper

**POST** `/research/deep_analyze_paper`

Run Noteweave's E3 two-pass critic on paper text. Uses a domain-expert reviewer persona (ML reviewer for AI, biologist for biology, clinician for medicine) to produce a structured critique.

### Request body
```json
{
  "text": "string (required, min 100 chars) — full paper text from fetch_paper_pdf",
  "title": "string — paper title",
  "domain": "auto",
  "pill": "string — domain pill for reviewer persona, e.g. artificial_intelligence, molecular_cellular_biology, clinical_medicine. Leave empty for generic reviewer."
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

### Example
```bash
# Step 1: fetch text
TEXT=$(curl -s -X POST https://api.noteweave.io/research/fetch_paper_pdf \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"arxiv_id": "1706.03762"}' | jq -r '.text')

# Step 2: analyze
curl -s -X POST https://api.noteweave.io/research/deep_analyze_paper \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"text\": $(echo $TEXT | jq -Rs .), \"pill\": \"artificial_intelligence\", \"title\": \"Attention Is All You Need\"}" \
  | jq -r '.review'
```

### Save review to file
```bash
curl -s -X POST https://api.noteweave.io/research/deep_analyze_paper \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "title": "Paper Title", "pill": "artificial_intelligence"}' \
  | jq -r '.review' > analysis.md
```

---

## Tool 3 — deep_analyze_batch

**POST** `/research/deep_analyze_batch`

Analyze up to 10 papers concurrently. Much faster than sequential calls.

### Request body
```json
{
  "papers": [
    {
      "title": "string (required)",
      "text": "string (required, min 100 chars) — from fetch_paper_pdf",
      "pill": "artificial_intelligence",
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

### Example
```bash
curl -s -X POST https://api.noteweave.io/research/deep_analyze_batch \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "papers": [
      {"title": "Paper A", "text": "...", "pill": "artificial_intelligence"},
      {"title": "Paper B", "text": "...", "pill": "artificial_intelligence"}
    ]
  }' | jq '.results[] | {title, review_length: (.review | length)}'
```

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
