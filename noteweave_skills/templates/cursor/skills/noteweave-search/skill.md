---
name: noteweave-search
description: Search academic papers across arXiv, Semantic Scholar, OpenAlex, PubMed, bioRxiv and more. Use when the user asks to find papers, search literature, look up research, find related work, or explore a research topic.
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

Search across 12 academic providers simultaneously. Results are fusion-searched, deduplicated, and reranked.

### Request body
```json
{
  "query": "string (required) — free-text research query",
  "pill": "string — domain key, default: general. Options: general, artificial_intelligence, computer_science, data_science, molecular_cellular_biology, systems_biology, neuroscience_cognition, cancer_oncology, clinical_medicine, mental_health, public_health, pharmacology_drug_development, physics, astronomy_astrophysics, chemistry, materials_science, mathematics, statistics, economics_finance, social_sciences, psychology_behavior",
  "per_provider": "integer 1-50, default 10",
  "year_from": "integer (optional)",
  "year_to": "integer (optional)",
  "sort": "relevance | latest | top_cited | new — default: relevance",
  "providers": "comma-separated whitelist e.g. 'arxiv,s2,openalex' — omit for all"
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
      "source": "arxiv | s2 | openalex | pubmed | biorxiv | medrxiv | ...",
      "citation_count": 0
    }
  ],
  "total": 42
}
```

### Example
```bash
curl -s -X POST https://api.noteweave.io/research/search_papers \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "vision transformers image classification",
    "pill": "artificial_intelligence",
    "per_provider": 10,
    "sort": "top_cited"
  }' | jq '.papers[] | {title, year, arxiv_id, citation_count}'
```

### Tips
- Set `pill` to the research domain for better provider routing (e.g. `molecular_cellular_biology` routes to PubMed, bioRxiv; `artificial_intelligence` routes to arXiv, S2)
- Call multiple times with different queries for broader coverage
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
