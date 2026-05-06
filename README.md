# noteweave-skills

Install [Noteweave](https://noteweave.io) research API skills into your AI coding agent — Cursor, Claude Code, Windsurf, Zed, and others.

Gives your agent access to:
- **Paper search** — fusion search across arXiv, Semantic Scholar, OpenAlex, PubMed, bioRxiv, and 7 more
- **PDF extraction** — download and read any paper
- **Deep analysis** — E3 two-pass expert critique with domain-specific reviewer personas
- **Dataset search** — HuggingFace + Kaggle
- **Experimental planning** — synthesize paper analyses into step-by-step `instructions.md`

## Install

```bash
pip install noteweave-skills
# or
uv add noteweave-skills
```

## Setup

Run in your project root:

```bash
noteweave-skills
```

The CLI asks which IDE you use and drops the right files:

| IDE | What gets installed |
|---|---|
| Cursor | `.cursor/skills/noteweave-*/skill.md` — auto-triggers + `/noteweave-search`, `/noteweave-analyze`, `/noteweave-write` slash commands |
| Claude Code | `NOTEWEAVE.md` + adds `@NOTEWEAVE.md` to `CLAUDE.md` |
| Windsurf | `NOTEWEAVE.md` + appends to `.windsurfrules` |
| Zed | `NOTEWEAVE.md` + adds note to `.zed/settings.json` |
| Other | `NOTEWEAVE.md` in project root |

Then set your token:

```bash
export NOTEWEAVE_TOKEN="nw_ext_..."
```

Get a token at [apps.noteweave.io/dashboard/tokens](https://apps.noteweave.io/dashboard/tokens) → Generate Token.

## Usage

Once installed, just ask your agent naturally:

> "Search for papers on vision transformers for medical imaging"

> "Fetch and analyze this paper: arxiv 2105.05537"

> "Analyze these 5 papers and generate an experimental plan"

The agent reads the installed skill/rules files and knows exactly how to call the Noteweave API.

## Rate limits

| Endpoint | Per minute | Per hour |
|---|---|---|
| search_papers | 20 | 200 |
| fetch_paper_pdf | 10 | 100 |
| deep_analyze_paper | 5 | 50 |
| deep_analyze_batch | 2 | 20 |
| search_datasets | 20 | 200 |
| write_instructions | 5 | 30 |

## License

MIT
