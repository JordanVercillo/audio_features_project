# Roadmap — build order

Tick items as they land. Durable conventions live in `PROJECT_CONTEXT.md`; this
is the plan. Keep it forward-looking; every phase ends with a checkable outcome.

**The one-sentence version:** The weekly MusicBrainz pipeline runs unattended, Jordan's Spotify top tracks and artists resolve to MusicBrainz records, local audio features are extracted for those tracks, and a dashboard plus a dedicated section on vercilloanalytics.com present it all.

- [x] ✅ **Phase 1 — The spec and the dataflow diagram** — *merged 2026-11-07 (PR #1, fabc8ee, CI green); the spec is APPROVED*
  `specs/music_data_platform_spec.yaml` (validates; 16 owner rulings in its decision log) and `docs/dataflow.md`. · *Proven:* the spec validates (`validate_spec.py` ✅), the dataflow diagram is committed under `docs/` (✅), every open question has a ruling or a named owner (✅ six entries), the PR is merged (✅).
- [ ] 📍 **Phase 2 — MusicBrainz foundation** (the spec's `task_2`, `task_3`, `task_4`)
  Slice 1: `/spark-env`, the dbt project (dbt Core + dbt-spark session, targets dev/prd, `models/<layer>/<source>/`), `src/audio_features/` skeleton. Slice 2: `scripts/fetch_musicbrainz.py` with the table allowlist, synthetic tests, and the audit's HARNESS change (environment root, source level, quarantine ratios; parity moves to dbt tests). Slice 3: `cleansed_musicbrainz` and `staging_musicbrainz` models with dbt tests and the synthetic-build test. **20% checkpoint:** a reviewer session at the entry state the spec names; it re-confirms the PROPOSED modeling defaults.
- [ ] **Phase 3 — Modeled and report layers** (`task_5`, `task_6`)
  The star schema (dims, bridges, `fact_tracks`, `fact_releases`, `dim_dates`) and the report marts the dashboard reads.
- [ ] **Phase 4 — Spotify integration** (`task_7`, re-specced first)
  Top tracks and artists over PKCE (reuse the predecessor's client), resolved to MusicBrainz as the source of truth (ISRC, then musicbrainz ids and the gid_redirect tables); `fact_top_tracks`; the match rate joins the audit.
- [ ] **Phase 5 — Audio features** (`task_8`, re-specced first)
  librosa extraction for Jordan's tracks only, idempotent and reliable, kept simple; the predecessor's extractor is the starting point.
- [ ] **Phase 6 — Dashboard, site page, promotion, go-live** (`task_9`)
  Streamlit over `data/prd/report/music/` via DuckDB, the first `promote <dump>` PR to `prd`, the webresume page. **80% checkpoint:** a reviewer session at the entry state the spec names, before the page is published.

## Immediate next step

Phase 2 slice 1, `tasks.task_2` of the spec, on a branch off `main`: `/spark-env` for local PySpark 3.5.6 (Windows + WSL), then the dbt project (dbt-core + dbt-spark[session], targets dev/prd, `models/<layer>/<source>/`, the `generate_schema_name` override, the `data_root` var), `src/audio_features/spark_session.py` and `layers.py`; proven by `uv run dbt debug --target dev` and the duplicate-name parse test; one reviewed PR. Nothing blocks it.
