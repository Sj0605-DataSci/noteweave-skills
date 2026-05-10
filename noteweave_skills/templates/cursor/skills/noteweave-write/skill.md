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

## Cache check (read first)

Before calling, check whether the answer already exists on disk:

- If `.noteweave/instructions.md` exists for the same brief (compare against `.noteweave/brief.json`), reuse it instead of re-generating.
- If individual papers have not yet been analyzed (`.noteweave/papers/<slug>/analysis.md` missing), run `noteweave-analyze` first — `write_instructions` requires at least one paper with populated `analysis_text`.

Only call the live API when cache is missing or the brief has changed.

---

## Tool — write_instructions

**POST** `/research/write_instructions`

Synthesizes E3 paper reviews + your research brief into a step-by-step experimental plan. Returns Markdown — save it to `.noteweave/instructions.md` in your workspace.

### Request body
```json
{
  "brief": {
    "system_description": "<one-sentence description of the system being built>",
    "primary_metric": "<metric being optimized>",
    "current_value": "<current number>",
    "target_value": "<target number>",
    "dataset": "<dataset name>",
    "tried_so_far": "<approaches already attempted>",
    "prior_results": "<results from prior attempts>",
    "hardware": "<hardware spec>",
    "timeline_days": "<integer days>",
    "failure_condition": "<when to stop>",
    "current_method": "string (optional)",
    "current_library": "string (optional)",
    "domain": "string (optional)",
    "falsifiable_question": "string (optional)"
  },
  "papers": [
    {
      "title": "<exact paper title>",
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
        "analysis_text": "... (from deep_analyze_paper) ...",
        "arxiv_id": "<arxiv id>"
      }
    ]
  }' | jq -r '.instructions_md' > .noteweave/instructions.md
```

---

## Persistence

After `write_instructions`:

1. Save the returned Markdown to `.noteweave/instructions.md` (overwrites any prior plan; the user can `git diff` to see what changed).
2. Optionally archive the previous version to `.noteweave/instructions.<timestamp>.md` if it exists, so the user can compare iterations.

The brief itself (the JSON payload) should be saved to `.noteweave/brief.json` so subsequent calls can re-use it without the user re-stating their goal.

---

## Rate limits (per user)
| Endpoint | Per minute | Per hour |
|---|---|---|
| write_instructions | 5 | 30 |

HTTP 429 → rate limited, check `Retry-After` header.
HTTP 402 → token quota exhausted, upgrade at https://apps.noteweave.io/dashboard/billing.
HTTP 504 → job timed out, retry once.
