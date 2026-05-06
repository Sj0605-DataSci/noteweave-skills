---
name: noteweave-write
description: Generate an experimental research plan (instructions.md) from analyzed papers and a research brief. Use when the user wants to plan an experiment, generate research instructions, create an experimental roadmap, or synthesize paper analyses into an action plan.
---

# Noteweave Write Instructions

## Auth
Every request needs: `Authorization: Bearer $NOTEWEAVE_TOKEN`

Get your token: https://apps.noteweave.io/dashboard/tokens → "Generate Token"

Base URL: `https://api.noteweave.io`

---

## Full workflow to get instructions.md

```
1. search_papers       → find relevant papers
2. fetch_paper_pdf     → get text for each paper
3. deep_analyze_paper  → get E3 review for each paper
4. write_instructions  → synthesize into experimental plan
5. save to instructions.md in workspace
```

---

## Tool — write_instructions

**POST** `/research/write_instructions`

Synthesizes E3 paper reviews + your research brief into a step-by-step experimental plan. Returns Markdown — save it to `instructions.md` in your workspace.

### Request body
```json
{
  "brief": {
    "system_description": "string (required) — what system you're building or improving",
    "primary_metric": "string — metric to optimise, e.g. 'F1 score', 'mAP', 'perplexity'",
    "current_value": 0.0,
    "target_value": 0.0,
    "dataset": "string — dataset name",
    "tried_so_far": "string — approaches already attempted",
    "prior_results": "string — results from prior attempts",
    "hardware": "1x A100 GPU",
    "timeline_days": 14,
    "failure_condition": "No improvement after 3 runs",
    "current_method": "string (optional)",
    "current_library": "string (optional)",
    "domain": "string (optional)",
    "falsifiable_question": "string (optional)"
  },
  "papers": [
    {
      "title": "string (required)",
      "analysis_text": "string (required for at least one paper) — review from deep_analyze_paper",
      "abstract": "string (optional)",
      "authors": ["string"],
      "year": 2024,
      "citation_count": 150,
      "arxiv_id": "string or null",
      "url": "string or null"
    }
  ]
}
```

**At least one paper must have `analysis_text` populated from `deep_analyze_paper`.**

### Response
```json
{
  "instructions_md": "string — full experimental plan in Markdown"
}
```

### Example
```bash
curl -s -X POST https://api.noteweave.io/research/write_instructions \
  -H "Authorization: Bearer $NOTEWEAVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brief": {
      "system_description": "Image segmentation model for medical CT scans",
      "primary_metric": "Dice score",
      "current_value": 0.72,
      "target_value": 0.82,
      "dataset": "BTCV",
      "tried_so_far": "UNet baseline, basic augmentation",
      "hardware": "2x A100 GPUs",
      "timeline_days": 14
    },
    "papers": [
      {
        "title": "Swin-UNet",
        "analysis_text": "... (from deep_analyze_paper) ...",
        "arxiv_id": "2105.05537"
      }
    ]
  }' | jq -r '.instructions_md' > instructions.md
```

---

## Rate limits (per user)
| Endpoint | Per minute | Per hour |
|---|---|---|
| write_instructions | 5 | 30 |

HTTP 429 → rate limited, check `Retry-After` header.
HTTP 402 → token quota exhausted, upgrade at https://apps.noteweave.io/dashboard/billing.
HTTP 504 → job timed out, retry once.
