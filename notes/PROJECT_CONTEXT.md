# PROJECT CONTEXT — read this first

## ⏭️ RESUME HERE (30-second orientation)

- **Project:** audio_features — a weekly-refreshed MusicBrainz warehouse (ingest → cleansed → staging → modeled → report) as dbt models on local Spark, laid out `data/<environment>/<layer>/<source>/<table>/`, joined to Jordan's Spotify history and local audio features, presented in a Streamlit dashboard and a page on vercilloanalytics.com. Supersedes `audio-agentic-pipeline`.
- **Status:** Phase 2 slice 1 (`tasks.task_2`) is merged: PR #5 (`slice/phase2-engine` → `main`; code-reviewer APPROVE ×3) landed 2026-11-07 as 3a8b136, CI green on `main` with `15 passed`; the owner then ran `scripts\spark_wsl.ps1 -Verify` and got VERIFIED. The engine exists: pyspark 3.5.6 + dbt-core 1.12.6 + dbt-spark 1.11.0 pinned, `src/audio_features/{layers,spark_session}.py`, `dbt_project.yml` + a committed `profiles.yml` (session method, targets dev/prd, one Derby metastore per target), the verbatim `generate_schema_name` macro, the four `models/<layer>/<source>/` folders, the WSL launcher `scripts/spark_wsl.ps1`. Windows is the debug/parse/compile host (no winutils, so Spark there cannot write); WSL is the build host. Still no data: `/warehouse-audit` reports `NO_DATA`. Open issues: #2 (`set_monitor` denied again; `gh pr create` now works), #3 (rulings after review), #4 (task_2's "musicbrainz folder in each layer" wording vs the modeled_music / report_music ruling).
- **➡️ NEXT ACTION —** Phase 2 slice 2, `tasks.task_3` of the spec, on a branch off `main` (PR #5 is merged; nothing blocks the start): `scripts/fetch_musicbrainz.py` with the table allowlist at `src/audio_features/musicbrainz_tables.yaml` (the spec's first open question — the exact allowlist per archive with primary keys, roles and columns — is ruled or taken as PROPOSED first), the synthetic-tarball tests in `tests/test_fetch_musicbrainz.py` (no network), and the audit's HARNESS part (environment root, source level, the manifest's new path, quarantine ratios, LAYER_PARITY retired, `data/<env>/spark-warehouse/` skipped). Rulings to take on the way: #4; the WSL shuffle-spill dir (`/tmp` is tmpfs there; REC `/var/tmp`, one constant in `spark_session.py`); an allow-rule for `mcp__ccd_pr__set_monitor` so auto-fix can be turned on (#2). Anything that writes Parquet runs in WSL: `scripts\spark_wsl.ps1 -Run "dbt build --target dev"`.
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
- Two hosts, one toolchain (pyspark 3.5.6 on CPython 3.11 on both). Windows has no winutils, so Spark there starts, parses, compiles and serves the catalog but cannot write files or create a Hive database: `dbt debug`, `dbt parse`, `dbt compile` and the JVM-free tests run on Windows; `dbt build`, the Parquet-writing test and anything else that writes run in WSL through `scripts/spark_wsl.ps1 -Run "<uv run args>"` (`-Setup` once per machine; the WSL venv is `~/.venvs/audio-features`, outside the repo, and `-Run` is `--frozen` so WSL never rewrites `uv.lock`). The Spark settings have one home: `profiles.yml` → `server_side_parameters`, plain literals (no Jinja) that dbt-spark and `build_spark()` both apply; `dbt_project.yml`'s `+location_root` default is absolute through `flags.PROFILES_DIR` because Spark re-roots a relative table location under the database folder. One dbt build at a time (Derby).

## Key files

| Path | What it is |
|---|---|
| `CLAUDE.md` | bootloader — ground rules + routing + map |
| `specs/music_data_platform_spec.yaml` | the platform spec (Phase 1): decisions with reasoning, tasks per phase, verification lines tagged CI / local, open questions with owners, the dated decision log |
| `docs/dataflow.md` | the Mermaid dataflow diagram; its notes are pointers into the spec |
| `notes/journal.md` | numbered lessons (surprises worth remembering) |
| `notes/roadmap.md` | the build order / plan, with the 20% and 80% checkpoints |
| `pyproject.toml` · `uv.lock` | the pins (pyspark 3.5.6 exact; dbt-core 1.12.x; dbt-spark[session] 1.11.x) and the editable install of `src/audio_features` (uv_build); `uv lock` on Windows after any dependency change |
| `src/audio_features/layers.py` · `spark_session.py` | ENVIRONMENTS, LAYERS (pinned to the audit's literal by test) and the `data/<environment>/<layer>/<source>/<table>` paths; `build_spark(environment)`, the one SparkSession builder (reads `profiles.yml`, overrides PYSPARK_PYTHON per process) |
| `dbt_project.yml` · `profiles.yml` · `macros/generate_schema_name.sql` | the dbt project: per-folder `+schema` and `+location_root`, Parquet tables; the committed profile (no secrets) with each target's Spark settings; the schema returned verbatim |
| `scripts/spark_wsl.ps1` + `spark_wsl_bootstrap.sh` | the WSL build host: `-Check`, `-Setup`, `-Verify` (known answers incl. a Parquet write and a Hive CTAS), `-Run "<uv run args>"` |
| `tests/test_dbt_project.py` · `tests/test_layers.py` | the task_2 proofs: duplicate bare name fails `dbt parse`, the alias compiles to `cleansed_musicbrainz.artists`, `dbt build` writes bare tables under `<data_root>/<layer>/<source>/` and overwrites (Linux only; CI and WSL) |
| `.claude/skills/warehouse-audit/audit_warehouse.py` | the deterministic audit: dump freshness vs `LATEST`, layer presence and order, row-count parity (parity retires in Phase 2 slice 2, when the audit learns the environment and source levels and quarantine ratios — `tasks.task_3`) |
| `C:\Users\jverc\audio-agentic-pipeline` | the predecessor: Spotify PKCE client, librosa extraction — read and reuse, never import |
| `C:\Users\jverc\webresume\projects\audio-features.md` | the project's page on vercilloanalytics.com (rebuild and commit there) |
| https://data.metabrainz.org/pub/musicbrainz/data/fullexport/ | the MusicBrainz source: dated dump folders + `LATEST` (20261104-002222 on 2026-11-06); the refresh takes mbdump, mbdump-derived, mbdump-cover-art-archive |
| https://github.com/metabrainz/musicbrainz-server | `lib/MusicBrainz/Server/Constants.pm` is the authority on which table is in which archive |

## Session log

- **2026-11-05** — Bootstrapped the Claude Code harness from the harness kit (plugin 0.2.0; tiers: core, gates, specs, lead, domain). Ruled: solo, reviewed PRs, loose skill copies, `/warehouse-partner` + `/warehouse-audit`. **Left off:** run `/spec music data platform`.
- **2026-11-06** — Repo moved to the GitHub clone `audio_features_project` (byte-identical). `/spec music data platform`: 16 owner rulings (three archives; allowlisted ingest; dbt Core + dbt-spark session; `environment/layer_source/table` mirrored on disk; plural tables, singular structs, names never repeated across layers; cleansed renames, staging joins; dev/prd with `main` as dev; fact_tracks + fact_releases; Streamlit + DuckDB; the webresume page). Data-modeling seat verified the allowlist against the musicbrainz-server source (genre is core, not derived); testing seat found dbt's unique-node-name rule; code-reviewer APPROVE after two rounds. Branch `spec/music-data-platform`, 3 commits, pushed; the auto-mode classifier denied `gh pr create`, so the PR opens through the app. **Left off:** owner opens and merges the spec PR; then Phase 2 slice 1 (`tasks.task_2`).
- **2026-11-07** — PR #1 opened through the app's create_pr action (the classifier also denied `gh pr create` alone and `set_monitor`, so auto-fix stayed off), CI green, merged by the owner as fabc8ee. This wrap flipped the spec to APPROVED, deleted the merged branch and filed the two frictions as issues. **Left off:** Phase 2 slice 1 (`tasks.task_2`): `/spark-env`, the dbt project, the package skeleton.
- **2026-11-07 (2)** — Phase 2 slice 1 built through `/orchestrator` (python-expert → sql-expert → testing-expert → code-reviewer, one at a time): pins resolved exactly to the spec's lines; Windows proven unable to write Parquet (no winutils) so WSL became the build host with an adapted launcher; `profiles.yml` made the one home of the Spark settings; a relative `+location_root` was found buried under `spark-warehouse/` and the default made absolute; every task_2 proof became a test seen failing first; `uv run pytest` was found running the pre-move checkout's venv (stale `.exe` launchers, fixed by `uv sync --reinstall`). Reviewer APPROVE with 4 MINORs → fixed → APPROVE → 1 MINOR → fixed → APPROVE. PR #5 opened with `gh pr create` (allowed this time); `set_monitor` denied again. CI green, `15 passed`. Issue #4 filed (task_2 wording). Journal #3–#5. **Left off:** owner merges PR #5; then slice 2 (`tasks.task_3`): the fetch, the allowlist, the audit's HARNESS part.
