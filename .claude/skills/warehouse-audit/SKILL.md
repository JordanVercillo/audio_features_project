---
name: warehouse-audit
description: Internal skill — deterministic audit of the audio_features warehouse. Called by warehouse-partner at session start and after any layer rebuild or new MusicBrainz dump; also usable directly when the owner asks to "audit the warehouse", "is the data current", or "is the warehouse healthy".
user-invocable: true
allowed-tools: [Bash, Read]
---

You are an audit agent. Run the validator, then report; no design opinions.

## Steps

1. From the repo root run:

   ```bash
   uv run .claude/skills/warehouse-audit/audit_warehouse.py
   ```

   (`--offline` skips the `LATEST` lookup on data.metabrainz.org; CI uses it.)

2. Parse the JSON output and return exactly this block:

   ```
   === WAREHOUSE AUDIT ===
   Dump: <loaded dump id or "none"> · LATEST: <remote id, "unreachable" or "skipped"> · Layers: <present>/5 · Tables: <n> · Rows: <total>
   Errors:   <one line each, or "none">
   Warnings: <one line each, or "none">
   Flags:    <true flags with [WARNING], or "Normal">
   ```

3. Flag meanings (one line per flag the script can emit):
   - `NO_DATA` — `data/` has no layer yet (informational; blocks every layer-dependent slice: the roadmap item that creates the ingest layer IS the session)
   - `DUMP_STALE` [WARNING] — the loaded dump (`data/ingest/_manifest.json`) is not the `LATEST` on data.metabrainz.org; the weekly refresh is due before any analysis is reported
   - `NO_MANIFEST` [WARNING] — an ingest layer exists but no `_manifest.json` names its dump; freshness cannot be judged until the ingest writes one
   - `LAYER_MISSING` [WARNING] — a later layer exists while an earlier one is absent; layers are rebuilt in order, so the missing one blocks the ones above it
   - `LAYER_PARITY` [WARNING] — a table's row count drops by more than the threshold (default 20%) between adjacent layers; either the drop is explained in the dbt model's description or it is a defect (retired in Phase 2 when names stop repeating across layers; the dbt row-count tests take over)

If the script itself errors, report the raw error and stop; do not guess. Return only the
formatted block, no commentary.
