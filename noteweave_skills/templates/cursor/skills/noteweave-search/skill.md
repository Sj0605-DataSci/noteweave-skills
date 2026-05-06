---
name: noteweave-search
description: Search academic papers across arXiv, Semantic Scholar, OpenAlex, PubMed, bioRxiv and more. Use when the user asks to find papers, search literature, look up research, find related work, explore a research topic, or find papers from a specific conference or journal.
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

Search across 12 academic providers simultaneously. Results are fusion-searched, deduplicated, and reranked by GPT-5-nano relevance scoring.

### Request body
```json
{
  "query": "string (required) — free-text research query",
  "pill": "string — domain key, default: general. Options: general, artificial_intelligence, computer_science, data_science, molecular_cellular_biology, systems_biology, neuroscience_cognition, cancer_oncology, clinical_medicine, mental_health, public_health, pharmacology_drug_development, physics, astronomy_astrophysics, chemistry, materials_science, mathematics, statistics, economics_finance, social_sciences, psychology_behavior",
  "per_provider": "integer 1-50, default 10",
  "year_from": "integer (optional)",
  "year_to": "integer (optional)",
  "sort": "relevance | latest | top_cited | new — default: relevance",
  "providers": "comma-separated whitelist e.g. 'arxiv,s2,openalex' — omit for all",
  "venue": "string (optional) — conference or journal name e.g. 'NeurIPS', 'CVPR 2023', 'Nature Medicine'. When set, Semantic Scholar runs first with a boosted result cap."
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
      "citation_count": 0,
      "venue": "string or null — journal or conference name (null for arXiv preprints)",
      "rank": 1
    }
  ],
  "total": 42,
  "providers": {"s2": 8, "openalex": 6, "arxiv": 5}
}
```

`rank` is 1-based — lower = more relevant (assigned by GPT-5-nano reranker).
`providers` shows how many papers came from each source.

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

### Example — conference-filtered search
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

### Tips
- Set `pill` to the research domain for better provider routing
- Use `venue` when the user asks for papers from a specific conference (NeurIPS, CVPR, ICML, ICLR, ACL, EMNLP, Nature, Science, etc.) or journal
- Use `arxiv_id` or `pdf_url` from results as input to `fetch_paper_pdf`
- `providers` in the response shows source distribution — useful for debugging coverage

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
