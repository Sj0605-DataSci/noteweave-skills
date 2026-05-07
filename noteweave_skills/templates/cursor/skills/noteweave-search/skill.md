---
name: noteweave-search
description: Search academic papers across the Noteweave research index. Use when the user asks to find papers, search literature, look up research, find related work, explore a research topic, or find papers from a specific conference or journal.
---

# Noteweave Paper & Dataset Search

## Auth
Every request needs: `Authorization: Bearer $NOTEWEAVE_TOKEN`

Get your token: https://apps.noteweave.io/dashboard/tokens → "Generate Token"
Store it as `NOTEWEAVE_TOKEN` in your environment or `.env` file.

Base URL: `https://api.noteweave.io`

---

## Tool 1 — search_papers

**POST** `/research/search_papers`

Search the Noteweave research index. Returns ranked, deduped papers with citation counts and venue metadata where available.

### Request body
```json
{
  "query": "string (required) — free-text research query",
  "pill": "string — research domain. Default: general. Options: general, artificial_intelligence, computer_science, data_science, molecular_cellular_biology, systems_biology, neuroscience_cognition, cancer_oncology, clinical_medicine, mental_health, public_health, pharmacology_drug_development, physics, astronomy_astrophysics, chemistry, materials_science, mathematics, statistics, economics_finance, social_sciences, psychology_behavior",
  "per_provider": "integer 1-50, default 10",
  "year_from": "integer (optional)",
  "year_to": "integer (optional)",
  "sort": "relevance | latest | top_cited | new — default: relevance",
  "providers": "comma-separated whitelist e.g. 'arxiv,s2,openalex' — omit for default search",
  "venue": "string (optional) — conference or journal name e.g. 'NeurIPS', 'CVPR 2023', 'Nature Medicine'. Filters results by venue."
}
```

### Response
```json
{
  "papers": [
    {
      "title": "string",
      "authors": ["string"],
      "year": 2024,
      "abstract": "string (up to 800 chars)",
      "arxiv_id": "string or null",
      "doi": "string or null",
      "url": "string or null",
      "pdf_url": "string or null",
      "source": "string — provider that surfaced the paper",
      "citation_count": 0,
      "venue": "string or null — journal or conference name",
      "rank": 1
    }
  ],
  "total": 42,
  "providers": {"arxiv": 8, "s2": 6}
}
```

`rank` is 1-based — lower = more relevant.
`providers` shows how many results came from each provider.

### Example — general search
```bash
curl -s -X POST https://api.noteweave.io/research/search_papers \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "vision transformers image classification",
    "pill": "artificial_intelligence",
    "per_provider": 10,
    "sort": "top_cited"
  }' | jq '.papers[] | {title, year, source, venue, rank, citation_count}'
```

### Example — venue-filtered search
```bash
curl -s -X POST https://api.noteweave.io/research/search_papers \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diffusion models image generation",
    "pill": "artificial_intelligence",
    "venue": "NeurIPS",
    "year_from": 2022
  }' | jq '.papers[] | {title, year, venue, rank}'
```

### Example — explicit providers
```bash
curl -s -X POST https://api.noteweave.io/research/search_papers \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "BQP oracle separation",
    "providers": "arxiv,s2"
  }' | jq '.papers[] | {title, source, rank}'
```

### Tips
- Set `pill` to the research domain for better category routing
- Use `venue` when the user asks for papers from a specific conference (NeurIPS, CVPR, ICML, ICLR, ACL, EMNLP, Nature, Science, etc.) or journal — much more precise than putting the venue name in the query string
- Use `providers=` only when the user explicitly named sources ("arxiv only", "just S2"); otherwise leave empty for the default search
- Use `arxiv_id` or `pdf_url` from results as input to `fetch_paper_pdf`

---

## Tool 2 — search_datasets

**POST** `/research/search_datasets`

Search HuggingFace and Kaggle for ML datasets.

### Request body
```json
{
  "query": "string (required) — dataset search query"
}
```

### Response
```json
{
  "datasets": [
    {
      "id": "owner/dataset-name",
      "source": "huggingface | kaggle",
      "title": "string or null",
      "url": "string or null",
      "snippet": "string or null"
    }
  ],
  "total": 5
}
```

### Example
```bash
curl -s -X POST https://api.noteweave.io/research/search_datasets \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "medical image segmentation CT scan"}' | jq '.datasets[]'
```

---

## Rate limits (per user)
| Endpoint | Per minute | Per hour |
|---|---|---|
| search_papers | 20 | 200 |
| search_datasets | 20 | 200 |

HTTP 429 means rate limited — check `Retry-After` header.
HTTP 402 means token quota exhausted — upgrade plan at https://apps.noteweave.io/dashboard/billing
