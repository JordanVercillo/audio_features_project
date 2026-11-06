# audio_features — a data-platform portfolio project: a weekly-refreshed MusicBrainz warehouse (ingest → cleansed → staging → modeled → report) built in Spark notebooks, joined to Jordan's Spotify history and local audio features, and presented in a dashboard and a dedicated section of vercilloanalytics.com

## ⏭️ RESUME HERE (read first, every session)

**Before anything else, read [`notes/PROJECT_CONTEXT.md`](notes/PROJECT_CONTEXT.md).**
It is the living memory — current status, conventions, key files, and the exact
next step. Reading it makes you fully caught up without re-deriving anything.
`/resume` reads it automatically; `/wrap-session` updates it at session end.

This repo supersedes `C:\Users\jverc\audio-agentic-pipeline` (Spotify PKCE client, librosa
feature extraction, medallion conventions): reuse from it by reading, never by importing it as a
dependency. It is NOT the website: vercilloanalytics.com is rendered by `C:\Users\jverc\webresume`.

## Ground rules

1. **Python runs through uv.** `uv run <script>` from the repo root — never bare `python`, never
   an activated venv. PySpark 3.5.6 on CPython 3.11, on both Windows and WSL, stood up with the
   `/spark-env` playbook. Transformations live in notebooks under `notebooks/`, one per layer hop,
   and every notebook runs clean top to bottom from an empty kernel.
2. **`data/` is rebuildable, gitignored and never hand-edited.** It holds the MusicBrainz dumps and
   every Parquet layer (`data/<layer>/<table>/`, layers: ingest, cleansed, staging, modeled,
   report); the notebooks and scripts are the artifact. The project's page on
   vercilloanalytics.com is published through `webresume` (`projects/<slug>.md` there, then its
   `uv run build.py`); its generated `site/` is never hand-edited.
3. **Secrets by name only.** Spotify is PKCE: no client secret exists anywhere in this project.
   `SPOTIPY_CLIENT_ID` and `SPOTIPY_REDIRECT_URI` come from a gitignored `.env`; `.env.example`
   lists the names. A hardcoded fallback IS a leak.
4. Commit small reviewable chunks and push regularly — the repo is its own backup.

## Routing

| Want | Use |
|---|---|
| Get back up to speed & continue (start here) | `/resume` (orients, writes the session brief, hands it to `/orchestrator`) |
| Lead this session's work from its brief | `/orchestrator` + the brief path or a one-line goal |
| Work the warehouse roadmap as a senior partner | `/warehouse-partner` (recall → audit → adapt → work → update memory) |
| Is the warehouse current and intact? | `/warehouse-audit` (dump freshness vs LATEST, layer presence, row-count parity) |
| Design a feature before building it | `/spec` + one-line idea (`/interview-me` rules its open questions) |
| End a session that did meaningful work | `/wrap-session` (reviews the brief, saves memory, tidies, runs `/retro` when the harness fought back) |
| Stop mid-task and continue in a fresh session | `/handoff` |
| Something is red, throws, or a check moved | `diagnose` (model-invoked; name it to force it) |
| Prove every check passes | `/verify` (it reads the commands from this file: `uv run pytest` · `uv run ruff check .` · `uv run scripts/harness_guards.py` · `uv run .claude/skills/warehouse-audit/audit_warehouse.py`) |
| Open a reviewed PR | `/ship` (the `code-reviewer` seat gates it; the owner merges) |
| Stand up local Spark (Windows + WSL) | `/spark-env` (user-scope playbook; canonical files live in `vercilloanalytics`) |
| Publish or update the project page on the site | edit `projects/<slug>.md` in `C:\Users\jverc\webresume`, rebuild there, commit there |

**Roster** (domain seats, `.claude/agents/`; advise by default, implement in-lane on a hand-off,
never commit): `data-modeling-expert` (grain, layer contracts, star schema) ·
`sql-expert` (Spark SQL against the layers) · `python-expert` (uv, the package, notebooks' helper
code) · `testing-expert` (pytest, the audit script, what "verified" means) ·
`code-reviewer` (the mandatory PR gate).

The harness skills under `.claude/skills/` were pasted from the harness kit and adapted here; an
improvement every repo wants goes back to the kit as generic process, never with this repo's
specifics. A new skill or seat gets its routing row here.

## Map

| Path | What |
|---|---|
| `notes/` | PROJECT_CONTEXT (memory) · journal (numbered lessons) · roadmap (plan) |
| `.claude/` | agents · hooks · rules · skills · settings (the hooks, the allowlist) — this repo's part of the harness |
| `specs/` | validated implementation contracts (`/spec`); the first is the platform spec (Phase 1) |
| `docs/` | the dataflow diagram and design notes (Phase 1) |
| `scripts/` | single-file tools with PEP 723 headers (`harness_guards.py` today; the weekly MusicBrainz fetch next) |
| `src/audio_features/` | the first-party package: the Spark session builder, layer helpers, the Spotify and librosa clients (created in Phase 2) |
| `notebooks/` | one notebook per layer hop, the transformations in the open (created in Phase 2) |
| `data/` | gitignored: MusicBrainz dumps + the Parquet layers; `data/ingest/_manifest.json` records which dump is loaded |
| `tests/` | pytest, synthetic data, no network |
