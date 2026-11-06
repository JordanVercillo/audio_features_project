# PROJECT CONTEXT — read this first

## ⏭️ RESUME HERE (30-second orientation)

- **Project:** audio_features — a weekly-refreshed MusicBrainz warehouse (ingest → cleansed → staging → modeled → report) in Spark notebooks, joined to Jordan's Spotify history and local audio features, presented in a dashboard and a section of vercilloanalytics.com. Supersedes `audio-agentic-pipeline`.
- **Status:** Harness installed 2026-11-05 (core, gates, specs, lead, domain). No code, no data, no spec yet. Phase 1 (the spec + dataflow diagram) is open; `/warehouse-audit` reports `NO_DATA`.
- **➡️ NEXT ACTION —** `/spec music data platform`: interview to a validated spec covering the five layers and their contracts, the weekly MusicBrainz fullexport refresh (which dump files, how `LATEST` is checked), the dataflow diagram, and the 20% / 80% reviewer checkpoints; `/interview-me` rules the open questions (dump subset vs. full, engine for the report layer, dashboard tool, the project's subdomain on vercilloanalytics.com).
- **How to work:** `/resume` to start warm; `/wrap-session` to save at the end.

---

**Purpose.** This is the master memory file — READ IT FIRST to recall where we
left off, without re-deriving anything from the code. Keep it a **map, not a
transcript**: concise and scannable, linking to depth rather than duplicating it.

**How to update this file (protocol).** At session end: (a) refresh **Status** and
**➡️ NEXT ACTION**, (b) note new key files/conventions, (c) append one dated
**Session log** line ending in "**Left off:** …". Record genuine surprises in
`journal.md` (not here). If a fact here is now wrong, fix it — don't leave it stale.

## Conventions

- Python runs through `uv run` from the repo root; PySpark 3.5.6 on CPython 3.11 on both Windows and WSL (`/spark-env`); transformations are notebooks under `notebooks/`, one per layer hop, run clean top to bottom.
- `data/<layer>/<table>/` holds the Parquet layers (ingest, cleansed, staging, modeled, report) and the MusicBrainz dumps; rebuildable, gitignored, never hand-edited; `data/ingest/_manifest.json` names the loaded dump. The site page is published through `webresume`, never by editing its `site/`.
- Secrets by name only: Spotify PKCE, no client secret; `.env` gitignored, `.env.example` committed. Every slice lands through a reviewed PR on `main` (the `code-reviewer` seat gates, Jordan merges); reviewer sessions at the 20% and 80% checkpoints.

## Key files

| Path | What it is |
|---|---|
| `CLAUDE.md` | bootloader — ground rules + routing + map |
| `notes/journal.md` | numbered lessons (surprises worth remembering) |
| `notes/roadmap.md` | the build order / plan, with the 20% and 80% checkpoints |
| `.claude/skills/warehouse-audit/audit_warehouse.py` | the deterministic audit: dump freshness vs `LATEST` on data.metabrainz.org, layer presence, per-table row-count parity |
| `C:\Users\jverc\audio-agentic-pipeline` | the predecessor: Spotify PKCE client, librosa extraction, medallion conventions — read and reuse, never import |
| `C:\Users\jverc\webresume\projects\audio-features.md` | the project's page on vercilloanalytics.com (rebuild and commit there) |
| https://data.metabrainz.org/pub/musicbrainz/data/fullexport/ | the MusicBrainz source: dated dump folders + `LATEST` (one line naming the current dump) |

## Session log

- **2026-11-05** — Bootstrapped the Claude Code harness from the harness kit (plugin 0.2.0; tiers: core, gates, specs, lead, domain). Ruled: solo, reviewed PRs, loose skill copies, `/warehouse-partner` + `/warehouse-audit`. git init, minimal `pyproject.toml`, nothing committed.
  **Left off:** run `/spec music data platform` to write and validate the Phase 1 spec.
