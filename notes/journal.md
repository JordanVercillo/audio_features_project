# Journal — numbered surprises worth remembering

One entry per genuine surprise: situation → **The realization:** → `>` takeaway.
Routine progress is NOT a journal entry; status lives in `PROJECT_CONTEXT.md`.
Entries are **numbered and append-only** so they can be cited (e.g. "journal #3").
Capture the surprise, not the fix — the fix is in git; the lesson rarely is.

## #1 — 2026-11-06 — dbt model names are unique per project, so "the folder is the layer" needs an alias

The owner ruled that tables carry no layer prefix (`models/staging/artists.sql`, not
`stg_artists`), and the first draft of the spec wrote it that way for every layer.
**The realization:** dbt refuses to parse two models with the same bare name in different
folders (`DuplicateResourceNameError`), so the file must carry the schema
(`cleansed_musicbrainz__artists.sql`) and `config(alias='artists')` keeps the table bare; and
dbt's default `generate_schema_name` prefixes a custom schema with the target schema, so the
project overrides it. The testing seat found this reading docs, not running dbt.

> A naming ruling about tables is also a ruling about files and schemas; check the tool's
> uniqueness rules before the convention freezes.

## #2 — 2026-11-06 — the archive a MusicBrainz table lives in is a fact in Constants.pm, not in memory

The draft allowlist put `genre` in `mbdump-derived` alongside the tags, from memory of the
schema. **The realization:** `lib/MusicBrainz/Server/Constants.pm` in musicbrainz-server lists
`genre` in `CORE_TABLE_LIST`; cover-art members are schema-qualified
(`mbdump/cover_art_archive.cover_art`); a table with zero rows is omitted from the tar
entirely; and five tables that exist in `CreateTables.sql` (`area_containment`,
`release_first_release_date`, …) are never exported. A fetch written from the draft would have
failed on its first run.

> For a dump's contents, read the exporter's own table lists; the schema docs describe the
> database, not the export.
