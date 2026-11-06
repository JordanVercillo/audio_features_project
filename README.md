# audio_features

A data-platform portfolio project by Jordan Vercillo. It builds a weekly-refreshed warehouse from the
public [MusicBrainz](https://musicbrainz.org/) full export, layer by layer (ingest → cleansed →
staging → modeled → report) in Spark notebooks, then joins Jordan's own Spotify listening history
and locally extracted audio features (librosa) to it, and presents the result in a dashboard and a
dedicated section of [vercilloanalytics.com](https://vercilloanalytics.com). The point is to show,
end to end and in the open, how a world-class integration is built: a dataflow diagram, layer
contracts, an idempotent weekly pipeline, deterministic audits, reviewed PRs, and an agentic
workflow with no tech debt left behind.

## Quick start

```bash
uv sync                                                    # Python 3.11 + the dev tools
uv run scripts/harness_guards.py                           # the harness's own hygiene checks
uv run .claude/skills/warehouse-audit/audit_warehouse.py   # is the warehouse current and intact?
```

Local Spark (Windows + WSL) is stood up with the `/spark-env` playbook; see `CLAUDE.md`.

## Working with Claude Code

This repo carries a Claude Code harness (skills, seats, hooks and rules under `.claude/`,
plus the living memory under `notes/`). Start a session with **`/resume`** —
it reads `notes/PROJECT_CONTEXT.md` (the living memory) and continues from the exact
next step. End meaningful sessions with **`/wrap-session`** to save context.

- `CLAUDE.md` — ground rules + routing (read by every session).
- `notes/PROJECT_CONTEXT.md` — status, conventions, key files, next step.
- `notes/journal.md` — lessons learned. `notes/roadmap.md` — the plan.

## Prerequisites

- Python 3.11 (uv fetches it), [uv](https://docs.astral.sh/uv/), Java 17 (for Spark), `gh` for PRs.
