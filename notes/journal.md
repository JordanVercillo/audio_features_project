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

## #3 — 2026-11-07 — Spark re-roots a relative table `location` under the database, not the cwd

The first `dbt build` with `+location_root: data/<target>/cleansed/musicbrainz` passed (PASS=2)
and wrote the tables to `data/dev/spark-warehouse/cleansed_musicbrainz.db/data/dev/cleansed/...`.
**The realization:** `SessionCatalog.makeQualifiedTablePath` joins a relative table location to
the database's location (`<warehouse.dir>/<schema>.db/`), while `spark.sql.warehouse.dir` and
Derby's `databaseName` resolve against the working directory; and `dbt_project.yml` has no
project-root variable, only `flags.PROFILES_DIR`, which is the repo root because `profiles.yml`
is committed there. A relative path is the right literal for two of the three settings and the
wrong one for the third.

> "It built" is not "it landed where the spec says": assert the files' path after the first
> build, and check which base each engine setting resolves against before choosing relative.

## #4 — 2026-11-07 — a moved checkout keeps the old venv's launchers, so `uv run pytest` ran another repo

The repo moved from `audio_features` to `audio_features_project` on 2026-11-06 with its `.venv`.
`uv run pytest` kept passing — the three audit tests need nothing from the venv — until the
new tests imported the package and failed with `ModuleNotFoundError`. **The realization:** a
venv's `Scripts/*.exe` launchers embed the absolute path of the interpreter they were generated
for; `pytest.exe` still pointed at `C:\Users\jverc\audio_features\.venv`, which still existed,
so every `uv run pytest` had been running the OLD checkout's Python. `dbt.exe`, generated after
the move, was fine. `uv sync --reinstall` regenerates them.

> After moving or copying a checkout, `uv sync --reinstall`; and a tool that passes
> suspiciously well is worth one `sys.executable` print.

## #5 — 2026-11-07 — in WSL, `/tmp` is RAM and vanishes between launcher calls; the rc files belong to another repo

A `dbt build --vars '{data_root: /tmp/...}'` run through the launcher passed, and the next call
could list nothing: WSL's `/tmp` is tmpfs and the idle distro is torn down between
`wsl.exe` invocations. Separately, `~/.profile` and `~/.bashrc` export
`UV_PROJECT_ENVIRONMENT=~/.venvs/va-wsl` for vercilloanalytics, so a bare `uv run` in this repo
from an interactive WSL shell lands in that repo's venv. **The realization:** on this machine,
WSL state that must outlive one command goes on `/mnt/c` or under `$HOME`, never `/tmp`; and a
per-repo venv variable is set per process by the repo's own launcher, never exported globally
(the global export was another repo's convenience and is this repo's hazard).

> Treat WSL as a fresh process each call: durable paths on `/mnt/c` or `$HOME`, environment set
> by the launcher, nothing assumed from the login shell.
