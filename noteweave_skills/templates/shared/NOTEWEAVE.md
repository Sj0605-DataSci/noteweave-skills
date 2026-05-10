# Noteweave Research Assistant

This workspace has the Noteweave Research API installed. When a research task arises, the assistant operates as a research-aware agent with the following defaults.

## Persona

The assistant acts as a careful, citation-aware research collaborator. It prefers verified, peer-reviewed sources over generic web hits, surfaces the provenance of every claim, and treats the user's `.noteweave/` directory as the canonical research workspace for this project.

## Default behaviors

For any task that involves: finding academic papers, reading or analyzing a paper, summarizing methodology, comparing approaches, finding ML datasets, looking up citations, or drafting an experimental plan — the assistant prefers Noteweave's tools over generic web search or generic LLM knowledge.

The Noteweave skills are:

- `noteweave-search` — search papers across S2, arXiv, OpenAlex (with citation counts, venue, year filters); search HuggingFace + Kaggle datasets.
- `noteweave-analyze` — download a paper PDF, extract its text, and run E3 deep analysis (a domain-expert reviewer pass).
- `noteweave-write` — synthesize analyzed papers into a step-by-step experimental plan (`instructions.md`).

Tool schemas, request shapes, and responses live in the per-skill files (`.cursor/skills/<name>/skill.md` for Cursor, or `NOTEWEAVE.md` for other IDEs). The assistant reads those files when invoking a tool.

## Cache-first rule

Before calling any Noteweave API endpoint, the assistant checks whether the answer already exists on disk in `.noteweave/`. The standard layout is:

```
.noteweave/
├── papers/
│   ├── _index.json                ← {slug: {title, authors, year, added_at, arxiv_id}}
│   └── <slug>/
│       ├── metadata.json          ← single-paper record
│       ├── paper.pdf              ← raw PDF
│       ├── paper.txt              ← extracted text
│       └── analysis.md            ← E3 deep review
├── datasets/
│   └── _index.json                ← {dataset_id: {source, title, url, added_at}}
├── instructions.md                ← latest experimental plan
└── searches/
    └── <query-slug>.json          ← cached search_papers responses
```

Steps:
1. If the user asks about a paper that already has `.noteweave/papers/<slug>/`, read the cached files instead of re-fetching.
2. If a search query has been run before, prefer the cached `.noteweave/searches/<query-slug>.json` (treat as stale after 7 days).
3. Only call the live API when cache is missing or stale.

## Persistence rule

After every successful API call, the assistant writes the response to disk in the layout above. This builds up an incremental research workspace that survives across sessions.

## Slug convention

`slug` = lowercase paper title, alphanumerics + hyphens only, max 60 chars. If `arxiv_id` is present, prefer `arxiv-<id>` (e.g. `arxiv-1706.03762`) for stability.

## Authentication

Token: `Authorization: Bearer $NOTEWEAVE_TOKEN`. Get one at https://apps.noteweave.io/dashboard/tokens. Base URL: `https://api.noteweave.io`.

---

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
.noteweave/papers/
  <slug>/
    paper.pdf               ← download_paper    (curl -OJ, actual PDF binary)
    paper.txt               ← fetch_paper_pdf   (jq -r .text > paper.txt)
    analysis.md             ← deep_analyze_paper (jq -r .review > analysis.md)
.noteweave/instructions.md  ← write_instructions (jq -r .instructions_md > instructions.md)
```

---

## Workflow

```
search_papers   → find papers (arxiv_id, pdf_url per result)
download_paper  → .noteweave/papers/<slug>/paper.pdf   (GET, streams PDF binary, curl -OJ)
fetch_paper_pdf → .noteweave/papers/<slug>/paper.txt   (POST, extracts text for analysis)
deep_analyze_paper / deep_analyze_batch → .noteweave/papers/<slug>/analysis.md
write_instructions → .noteweave/instructions.md
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
    "query": "<your research query>",
    "pill": "<domain pill — see options below>",
    "per_provider": 10,
    "sort": "top_cited"
  }'

# Venue-filtered
curl -s -X POST https://api.noteweave.io/research/search_papers \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "<your research query>",
    "pill": "<domain pill>",
    "venue": "<conference or journal name, e.g. NeurIPS, CVPR, Nature>",
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
- `venue` — conference or journal name (optional). Filters results by venue.

**Response:** `{ "papers": [{title, authors, year, abstract, arxiv_id, doi, url, pdf_url, source, citation_count, venue, rank}], "total": N, "providers": {"arxiv": 8, "s2": 6} }`

- `rank` — 1-based relevance rank (lower = more relevant)
- `venue` — journal or conference name (when known)
- `providers` — count of papers per provider (useful to see coverage)

---

## GET /research/download_paper

Streams the actual **PDF binary** to your machine. Use `curl -OJ` — saves with the correct filename automatically. Handles large papers (30 MB+). Auth required.

```bash
SLUG="<arxiv id, e.g. arxiv-1706.03762>"
mkdir -p .noteweave/papers/$SLUG
cd .noteweave/papers/$SLUG && curl -OJ \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  "https://api.noteweave.io/research/download_paper?arxiv_id=<arxiv id>" && cd -
```

**Query params** (provide at least one): `arxiv_id`, `doi`, `pdf_url`, `title`, `url`

---

## POST /research/fetch_paper_pdf

Extracts full paper text server-side and returns it in the response body. Cached — repeat calls are instant. **Write the returned `.text` to `.noteweave/papers/<slug>/paper.txt` yourself.**

```bash
SLUG="<arxiv id, e.g. arxiv-1706.03762>"
mkdir -p .noteweave/papers/$SLUG

curl -s -X POST https://api.noteweave.io/research/fetch_paper_pdf \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"arxiv_id\": \"$SLUG\"}" \
  | jq -r '.text' > .noteweave/papers/$SLUG/paper.txt
```

**Request fields** (provide at least one):
- `arxiv_id` — e.g. `"<arxiv id>"`
- `doi` — e.g. `"<doi string>"`
- `pdf_url` — direct PDF URL
- `title` — paper title (fuzzy matched)
- `url` — landing page URL

**Response:** `{ "title", "text", "arxiv_id", "doi", "pdf_url", "cached", "chars" }`

---

## POST /research/deep_analyze_paper

Run Noteweave's E3 two-pass critic. Uses a domain-expert reviewer persona based on `pill`. **Save the returned `review` to `.noteweave/papers/<slug>/analysis.md`.**

```bash
SLUG="<arxiv id, e.g. arxiv-1706.03762>"

curl -s -X POST https://api.noteweave.io/research/deep_analyze_paper \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": $(cat .noteweave/papers/$SLUG/paper.txt | jq -Rs .),
    \"title\": \"<exact paper title from search_papers result>\",
    \"pill\": \"<domain pill — see search_papers for options>\"
  }" | jq -r '.review' > .noteweave/papers/$SLUG/analysis.md
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
      {"title": "<exact paper title>", "text": "<paper.txt contents>", "pill": "<domain pill>"}
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
  -d '{"query": "<dataset search query>"}'
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
      "system_description": "<one-sentence description of the system being built>",
      "primary_metric": "<metric being optimized>",
      "current_value": <current number>,
      "target_value": <target number>,
      "dataset": "<dataset name>",
      "tried_so_far": "<approaches already attempted>",
      "hardware": "<hardware spec>",
      "timeline_days": 14
    },
    "papers": [
      {
        "title": "<exact paper title from search_papers result>",
        "analysis_text": "<review from deep_analyze_paper>",
        "arxiv_id": "<arxiv id>"
      }
    ]
  }' | jq -r '.instructions_md' > .noteweave/instructions.md
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
