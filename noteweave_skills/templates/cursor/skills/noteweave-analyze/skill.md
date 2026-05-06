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

## How papers land in your workspace

Two separate tools — use both together:

| Tool | What it does | Output |
|---|---|---|
| `download_paper` | Streams the actual **PDF binary** to your machine | `papers/<id>.pdf` |
| `fetch_paper_pdf` | Extracts full **text** from the PDF server-side | `papers/<id>/paper.txt` |

Always save both. Standard layout:
```
papers/
  2511.16825.pdf              ← from download_paper (curl -OJ)
  2511.16825/
    paper.txt                 ← from fetch_paper_pdf (jq -r .text)
    analysis.md               ← from deep_analyze_paper (jq -r .review)
instructions.md               ← from write_instructions
```

---

## Workflow

```
download_paper   →  papers/<id>.pdf          (actual PDF on disk)
fetch_paper_pdf  →  papers/<id>/paper.txt    (extracted text for analysis)
                 →  deep_analyze_paper
                 →  papers/<id>/analysis.md
                 →  write_instructions → instructions.md
```

---

## Tool 1 — download_paper

**GET** `/research/download_paper`

Streams the actual PDF binary to your machine. Use `curl -OJ` — it auto-saves
with the correct filename (e.g. `2511.16825.pdf`). Handles large papers (34 MB+).

### Query params (provide at least one)
- `arxiv_id` — e.g. `2511.16825`
- `doi` — e.g. `10.1145/3292500.3330681`
- `pdf_url` — direct PDF URL
- `title` — paper title (fuzzy matched)
- `url` — landing page URL

### Example
```bash
mkdir -p papers

# Downloads and saves as <arxiv_id>.pdf automatically
curl -OJ \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  "https://api.noteweave.io/research/download_paper?arxiv_id=2511.16825"
# → saves papers/... wait, -OJ saves in CWD, so cd first:

cd papers && curl -OJ \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  "https://api.noteweave.io/research/download_paper?arxiv_id=2511.16825" && cd ..
# → papers/2511.16825.pdf
```

---

## Tool 2 — fetch_paper_pdf

**POST** `/research/fetch_paper_pdf`

Fetches and extracts full paper text server-side. Large PDFs (100+ MB) are handled.
Cached server-side — repeat calls for the same paper are instant.

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
  "text": "string — full extracted paper text (pass to deep_analyze_paper)",
  "arxiv_id": "string or null",
  "doi": "string or null",
  "pdf_url": "string or null",
  "cached": true,
  "chars": 45000
}
```

### Full example — fetch + save to workspace
```bash
SLUG="1706.03762"
mkdir -p papers/$SLUG

# Fetch and save text locally
curl -s -X POST https://api.noteweave.io/research/fetch_paper_pdf \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"arxiv_id\": \"$SLUG\"}" \
  | tee /tmp/nw_fetch.json \
  | jq -r '.text' > papers/$SLUG/paper.txt

echo "Saved $(wc -c < papers/$SLUG/paper.txt) chars to papers/$SLUG/paper.txt"
```

---

## Tool 2 — deep_analyze_paper

**POST** `/research/deep_analyze_paper`

Run Noteweave's E3 two-pass critic. Uses a domain-expert reviewer persona (ML
reviewer for AI papers, biologist for biology, clinician for medicine).

### Request body
```json
{
  "text": "string (required, min 100 chars) — full paper text from fetch_paper_pdf",
  "title": "string — paper title",
  "domain": "auto",
  "pill": "artificial_intelligence"
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

### Full example — analyze + save review to workspace
```bash
SLUG="1706.03762"
TEXT=$(cat papers/$SLUG/paper.txt)

curl -s -X POST https://api.noteweave.io/research/deep_analyze_paper \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": $(echo "$TEXT" | jq -Rs .),
    \"title\": \"Attention Is All You Need\",
    \"pill\": \"artificial_intelligence\"
  }" \
  | jq -r '.review' > papers/$SLUG/analysis.md

echo "Analysis saved to papers/$SLUG/analysis.md"
```

### Combined one-shot: fetch + analyze + save both
```bash
SLUG="2511.16825"
TITLE="WorldGen: From Text to Traversable and Interactive 3D Worlds"
mkdir -p papers/$SLUG

# Step 1: fetch text → save locally
curl -s -X POST https://api.noteweave.io/research/fetch_paper_pdf \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"arxiv_id\": \"$SLUG\", \"title\": \"$TITLE\"}" \
  | jq -r '.text' > papers/$SLUG/paper.txt

# Step 2: analyze from saved text → save review
curl -s -X POST https://api.noteweave.io/research/deep_analyze_paper \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": $(cat papers/$SLUG/paper.txt | jq -Rs .),
    \"title\": \"$TITLE\",
    \"pill\": \"artificial_intelligence\"
  }" \
  | jq -r '.review' > papers/$SLUG/analysis.md
```

---

## Tool 3 — deep_analyze_batch

**POST** `/research/deep_analyze_batch`

Analyze up to 10 papers concurrently. Much faster than sequential calls.
Save each review to `papers/<slug>/analysis.md` after the call.

### Request body
```json
{
  "papers": [
    {
      "title": "string (required)",
      "text": "string (required, min 100 chars) — contents of paper.txt",
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
