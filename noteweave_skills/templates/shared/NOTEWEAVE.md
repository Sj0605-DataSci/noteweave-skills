# Noteweave Research API

Noteweave gives you access to academic paper search, PDF extraction, deep E3 paper analysis, dataset search, and experimental plan generation — all via REST.

## Setup

1. Get your token at https://apps.noteweave.io/dashboard/tokens → "Generate Token"
2. Store it: `export NOTEWEAVE_TOKEN="nw_ext_..."`
3. Base URL: `https://api.noteweave.io`
4. All requests: `Authorization: Bearer $NOTEWEAVE_TOKEN` + `Content-Type: application/json`

---

## Workspace file convention

```
papers/
  2511.16825.pdf            ← download_paper    (curl -OJ, actual PDF binary)
  2511.16825/
    paper.txt               ← fetch_paper_pdf   (jq -r .text > paper.txt)
    analysis.md             ← deep_analyze_paper (jq -r .review > analysis.md)
instructions.md             ← write_instructions (jq -r .instructions_md > instructions.md)
```

---

## Workflow

```
search_papers   → find papers (arxiv_id, pdf_url per result)
download_paper  → papers/<id>.pdf          (GET, streams PDF binary, curl -OJ)
fetch_paper_pdf → papers/<id>/paper.txt    (POST, extracts text for analysis)
deep_analyze_paper / deep_analyze_batch → papers/<id>/analysis.md
write_instructions → instructions.md
search_datasets (independent)
```

---

## POST /research/search_papers

Search the Noteweave research index. Returns ranked, deduped papers with citation counts and venue metadata where available.

```bash
curl -s -X POST https://api.noteweave.io/research/search_papers \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "vision transformers image classification",
    "pill": "artificial_intelligence",
    "per_provider": 10,
    "sort": "top_cited"
  }'

# Venue-filtered
curl -s -X POST https://api.noteweave.io/research/search_papers \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diffusion models image generation",
    "pill": "artificial_intelligence",
    "venue": "NeurIPS",
    "year_from": 2022
  }'
```

**Request fields:**
- `query` *(required)* — free-text research query
- `pill` — research domain. Options: `general`, `artificial_intelligence`, `computer_science`, `data_science`, `molecular_cellular_biology`, `systems_biology`, `neuroscience_cognition`, `cancer_oncology`, `clinical_medicine`, `mental_health`, `public_health`, `pharmacology_drug_development`, `physics`, `astronomy_astrophysics`, `chemistry`, `materials_science`, `mathematics`, `statistics`, `economics_finance`, `social_sciences`, `psychology_behavior`
- `per_provider` — 1–50, default 10
- `year_from` / `year_to` — integer year bounds (optional)
- `sort` — `relevance` | `latest` | `top_cited` | `new`
- `providers` — comma-separated whitelist e.g. `"arxiv,s2,openalex"` (optional). Set ONLY if user named specific sources; otherwise leave empty for the default search.
- `venue` — conference or journal name e.g. `"NeurIPS"`, `"CVPR 2023"`, `"Nature Medicine"` (optional). Filters results by venue.

**Response:** `{ "papers": [{title, authors, year, abstract, arxiv_id, doi, url, pdf_url, source, citation_count, venue, rank}], "total": N, "providers": {"arxiv": 8, "s2": 6} }`

- `rank` — 1-based relevance rank (lower = more relevant)
- `venue` — journal or conference name (when known)
- `providers` — count of papers per provider (useful to see coverage)

---

## GET /research/download_paper

Streams the actual **PDF binary** to your machine. Use `curl -OJ` — saves with the correct filename automatically. Handles large papers (30 MB+). Auth required.

```bash
# Saves as 2511.16825.pdf in current directory
curl -OJ \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  "https://api.noteweave.io/research/download_paper?arxiv_id=2511.16825"
```

**Query params** (provide at least one): `arxiv_id`, `doi`, `pdf_url`, `title`, `url`

---

## POST /research/fetch_paper_pdf

Extracts full paper text server-side and returns it in the response body. Cached — repeat calls are instant. **Write the returned `.text` to `papers/<id>/paper.txt` yourself.**

```bash
SLUG="1706.03762"
mkdir -p papers/$SLUG

curl -s -X POST https://api.noteweave.io/research/fetch_paper_pdf \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"arxiv_id\": \"$SLUG\"}" \
  | jq -r '.text' > papers/$SLUG/paper.txt
```

**Request fields** (provide at least one):
- `arxiv_id` — e.g. `"1706.03762"`
- `doi` — e.g. `"10.1145/3292500.3330681"`
- `pdf_url` — direct PDF URL
- `title` — paper title (fuzzy matched)
- `url` — landing page URL

**Response:** `{ "title", "text", "arxiv_id", "doi", "pdf_url", "cached", "chars" }`

---

## POST /research/deep_analyze_paper

Run Noteweave's E3 two-pass critic. Uses a domain-expert reviewer persona based on `pill`. **Save the returned `review` to `papers/<id>/analysis.md`.**

```bash
SLUG="1706.03762"

# Analyze from saved text, save review to workspace
curl -s -X POST https://api.noteweave.io/research/deep_analyze_paper \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": $(cat papers/$SLUG/paper.txt | jq -Rs .),
    \"title\": \"Attention Is All You Need\",
    \"pill\": \"artificial_intelligence\"
  }" | jq -r '.review' > papers/$SLUG/analysis.md
```

**Request fields:**
- `text` *(required, min 100 chars)* — full paper text from `fetch_paper_pdf`
- `title` — paper title
- `pill` — domain for reviewer persona (same options as search_papers)
- `domain` — `"auto"` (default, works for most cases)

**Response:** `{ "title", "review", "domain", "pill" }` — `review` is full structured markdown.

---

## POST /research/deep_analyze_batch

Analyze up to 10 papers concurrently. Faster than sequential calls.

```bash
curl -s -X POST https://api.noteweave.io/research/deep_analyze_batch \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "papers": [
      {"title": "Paper A", "text": "...", "pill": "artificial_intelligence"},
      {"title": "Paper B", "text": "...", "pill": "artificial_intelligence"}
    ]
  }'
```

**Response:** `{ "results": [{title, review, error}], "total": N }`

---

## POST /research/search_datasets

Search HuggingFace and Kaggle for ML datasets.

```bash
curl -s -X POST https://api.noteweave.io/research/search_datasets \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "medical image segmentation"}'
```

**Response:** `{ "datasets": [{id, source, title, url, snippet}], "total": N }`

---

## POST /research/write_instructions

Synthesize paper analyses + research brief → step-by-step `instructions.md`.
At least one paper must have `analysis_text` from `deep_analyze_paper`.

```bash
curl -s -X POST https://api.noteweave.io/research/write_instructions \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brief": {
      "system_description": "Medical image segmentation for CT scans",
      "primary_metric": "Dice score",
      "current_value": 0.72,
      "target_value": 0.82,
      "dataset": "BTCV",
      "tried_so_far": "UNet baseline",
      "hardware": "2x A100 GPUs",
      "timeline_days": 14
    },
    "papers": [
      {
        "title": "Swin-UNet",
        "analysis_text": "<review from deep_analyze_paper>",
        "arxiv_id": "2105.05537"
      }
    ]
  }' | jq -r '.instructions_md' > instructions.md
```

**Brief fields:** `system_description`*(required)*, `primary_metric`, `current_value`, `target_value`, `dataset`, `tried_so_far`, `prior_results`, `hardware`, `timeline_days`, `failure_condition`, `current_method`, `current_library`, `domain`, `falsifiable_question`

**Response:** `{ "instructions_md": "string" }`

---

## Rate limits (per user)

| Endpoint | Per minute | Per hour |
|---|---|---|
| search_papers | 20 | 200 |
| fetch_paper_pdf | 10 | 100 |
| download_paper | 10 | 100 |
| deep_analyze_paper | 5 | 50 |
| deep_analyze_batch | 2 | 20 |
| search_datasets | 20 | 200 |
| write_instructions | 5 | 30 |

- HTTP 429 → rate limited, wait `Retry-After` seconds
- HTTP 402 → quota exhausted, upgrade at https://apps.noteweave.io/dashboard/billing
- HTTP 504 → job timeout, retry once
- HTTP 401 → invalid/expired token, regenerate at https://apps.noteweave.io/dashboard/tokens
