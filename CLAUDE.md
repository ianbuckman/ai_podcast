# AI Podcast Monitor

## Overview
Monitor YouTube AI/tech podcast channels, extract transcripts, analyze with Claude, push insights to Lark Docs (default) or Notion (`--notion`).

## Architecture
- Python scripts in `scripts/` handle data fetching (RSS + transcripts)
- Claude Code skill at `.claude/skills/podcast/SKILL.md` orchestrates the workflow
- State tracked in `data/processed.json` (gitignored)
- Default sink: Lark Docs in the user's personal wiki library (`my_library`), one doc per episode, via `lark-cli docs +create`
- Alternate sink: Notion database "AI Podcast Insights" (triggered by `--notion`)

## Running
- User invokes `/podcast` to trigger the full workflow (default → Lark Docs)
- Add `--notion` to route output to Notion instead
- Python 3.9+ required with packages in requirements.txt
- Lark sink requires `lark-cli` installed and authenticated (`lark-cli auth login`)
- No API keys needed for ingestion (YouTube RSS + youtube-transcript-api are both free)

## Conventions
- All Python scripts output JSON to stdout, errors/warnings to stderr
- Scripts use absolute paths relative to PROJECT_ROOT
- Each script is independently runnable for debugging
