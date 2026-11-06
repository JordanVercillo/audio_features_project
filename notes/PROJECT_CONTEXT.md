# PROJECT CONTEXT — read this first

## ⏭️ RESUME HERE (30-second orientation)

- **Project:** audio_features — a weekly-refreshed MusicBrainz warehouse (ingest → cleansed → staging → modeled → report) as dbt models on local Spark, laid out `data/<environment>/<layer>/<source>/<table>/`, joined to Jordan's Spotify history and local audio features, presented in a Streamlit dashboard and a page on vercilloanalytics.com. Supersedes `audio-agentic-pipeline`.
- **Status:** Phase 1 done on branch `spec/music-data-platform`, pushed (3 commits past main, code-reviewer APPROVE, verify green): `specs/music_data_platform_spec.yaml` validates with 16 owner rulings in its decision log, `docs/dataflow.md` is the diagram, the harness text says dbt instead of notebooks. The PR is not open yet: `gh pr create` was denied by the auto-mode classifier, so it opens through the app's create_pr action (the filled PR body sits next to the closed session brief in the project data folder). No code, no data; `/warehouse-audit` reports `NO_DATA`.
- **➡️ NEXT ACTION —** (1) owner: open the PR for `spec/music-data-platform` (the app's create_pr action; `gh pr list --state open` shows whether it exists), merge it; the merge is the word that moves the spec to APPROVED, and the next wrap flips its `status:` line. (2) Then Phase 2 slice 1, `tasks.task_2` of the spec: `/spark-env` for local PySpark 3.5.6, the dbt project (dbt-core + dbt-spark[session], targets dev/prd, `models/<layer>/<source>/`, the `generate_schema_name` override, `data_root` var), `src/audio_features/spark_session.py` and `layers.py`; proven by `uv run dbt debug --target dev` and the duplicate-name parse test. Nothing else is blocked on the merge: the slice branches from main and reads the spec from the spec branch until it lands.
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

- Python runs through `uv run` from the repo root; PySpark 3.5.6 on CPython 3.11 on both Windows and WSL (`/spark-env`). Transformations are dbt models (dbt Core + dbt-spark `session`), one per table at `models/<layer>/<source>/<layer>_<source>__<table>.sql` aliased to the bare table; the ingest is `scripts/fetch_musicbrainz.py`; notebooks are exploration only. The naming rules (plural tables, singular structs, full-word aliases, a name never repeated across layers, keys `<entity>_id` / `<entity>_musicbrainz_id`) and the layer contracts live in the spec — one home.
- `data/<environment>/<layer>/<source>/<table>/` holds the Parquet layers (environments dev, prd; layers ingest, cleansed, staging, modeled, report); rebuildable, gitignored, never hand-edited; `data/<environment>/ingest/musicbrainz/_manifest.json` names the loaded dump. `main` is the knowledge base and the dev line; a protected `prd` branch is promoted from it by PR (from Phase 6). The site page is published through `webresume`, never by editing its `site/`.
- Secrets by name only: Spotify PKCE, no client secret; `.env` gitignored, `.env.example` committed. Every slice lands through a reviewed PR on `main` (the `code-reviewer` seat gates, Jordan merges); reviewer sessions at the 20% and 80% checkpoints, whose entry states the spec names.
- The spec is the contract: code reads it, never edits it; a design change goes back through `/spec`. PROPOSED numbers in it are re-confirmed at the 20% checkpoint.

## Key files

| Path | What it is |
|---|---|
| `CLAUDE.md` | bootloader — ground rules + routing + map |
| `specs/music_data_platform_spec.yaml` | the platform spec (Phase 1): decisions with reasoning, tasks per phase, verification lines tagged CI / local, open questions with owners, the dated decision log |
| `docs/dataflow.md` | the Mermaid dataflow diagram; its notes are pointers into the spec |
| `notes/journal.md` | numbered lessons (surprises worth remembering) |
| `notes/roadmap.md` | the build order / plan, with the 20% and 80% checkpoints |
| `.claude/skills/warehouse-audit/audit_warehouse.py` | the deterministic audit: dump freshness vs `LATEST`, layer presence and order, row-count parity (parity retires in Phase 2 slice 2, when the audit learns the environment and source levels and quarantine ratios — `tasks.task_3`) |
| `C:\Users\jverc\audio-agentic-pipeline` | the predecessor: Spotify PKCE client, librosa extraction — read and reuse, never import |
| `C:\Users\jverc\webresume\projects\audio-features.md` | the project's page on vercilloanalytics.com (rebuild and commit there) |
| https://data.metabrainz.org/pub/musicbrainz/data/fullexport/ | the MusicBrainz source: dated dump folders + `LATEST` (20261104-002222 on 2026-11-06); the refresh takes mbdump, mbdump-derived, mbdump-cover-art-archive |
| https://github.com/metabrainz/musicbrainz-server | `lib/MusicBrainz/Server/Constants.pm` is the authority on which table is in which archive |

## Session log

- **2026-11-05** — Bootstrapped the Claude Code harness from the harness kit (plugin 0.2.0; tiers: core, gates, specs, lead, domain). Ruled: solo, reviewed PRs, loose skill copies, `/warehouse-partner` + `/warehouse-audit`. **Left off:** run `/spec music data platform`.
- **2026-11-06** — Repo moved to the GitHub clone `audio_features_project` (byte-identical). `/spec music data platform`: 16 owner rulings (three archives; allowlisted ingest; dbt Core + dbt-spark session; `environment/layer_source/table` mirrored on disk; plural tables, singular structs, names never repeated across layers; cleansed renames, staging joins; dev/prd with `main` as dev; fact_tracks + fact_releases; Streamlit + DuckDB; the webresume page). Data-modeling seat verified the allowlist against the musicbrainz-server source (genre is core, not derived); testing seat found dbt's unique-node-name rule; code-reviewer APPROVE after two rounds. Branch `spec/music-data-platform`, 3 commits, pushed; the auto-mode classifier denied `gh pr create`, so the PR opens through the app. **Left off:** owner opens and merges the spec PR; then Phase 2 slice 1 (`tasks.task_2`).
