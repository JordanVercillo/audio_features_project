# Roadmap — build order

Tick items as they land. Durable conventions live in `PROJECT_CONTEXT.md`; this
is the plan. Keep it forward-looking; every phase ends with a checkable outcome.

**The one-sentence version:** The weekly MusicBrainz pipeline runs unattended, Jordan's Spotify top tracks and artists resolve to MusicBrainz records, local audio features are extracted for those tracks, and a dashboard plus a dedicated section on vercilloanalytics.com present it all.

- [ ] 📍 **Phase 1 — The spec and the dataflow diagram**
  `/spec` the platform: the five layers and their contracts, the weekly fullexport refresh, the Spotify and audio-feature joins as later slices, the dashboard and site section, the two checkpoints. `/interview-me` rules the open questions. · *Proven when:* the spec validates (`validate_spec.py`), the dataflow diagram is committed under `docs/`, and every open question has a ruling or a named owner.
- [ ] **Phase 2 — MusicBrainz foundation**
  A weekly fetch of the fullexport (`LATEST` → the dated dump) into `data/ingest/` as Parquet with `_manifest.json`; cleansed and staging notebooks in Spark via `/spark-env`; `/warehouse-audit` green on freshness and parity. **20% checkpoint:** a reviewer session on the first draft of the layers.
- [ ] **Phase 3 — Modeled and report layers**
  The star schema (artist, release, recording, the date dimension; the facts at a stated grain) and the report marts the dashboard reads.
- [ ] **Phase 4 — Spotify integration**
  Top tracks and artists over PKCE (reuse the predecessor's client), resolved to MusicBrainz as the source of truth (ISRC and MBID links); the match rate joins the audit.
- [ ] **Phase 5 — Audio features**
  librosa extraction for Jordan's tracks only, idempotent and reliable, kept simple; the predecessor's extractor is the starting point.
- [ ] **Phase 6 — Dashboard, site section, go-live**
  The dashboard over the report layer and the project's section on vercilloanalytics.com (through `webresume`). **80% checkpoint:** a reviewer session before go-live.

## Immediate next step

`/spec music data platform` — the Phase 1 spec, validated, with the dataflow diagram.
