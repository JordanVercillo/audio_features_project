"""The dbt project's two naming proofs (spec tasks.task_2), on a synthetic project in tmp_path.

1. Two models with the same bare name in two folders make `dbt parse` fail with the
   duplicate-name error (why the file is <layer>_<source>__<table>.sql, journal #1).
2. The aliased pair compiles to `cleansed_musicbrainz.artists` — no target-schema prefix,
   because macros/generate_schema_name.sql returns the folder's +schema verbatim.
3. `dbt build` lands both tables as Parquet at <data_root>/<layer>/<source>/<alias>/ and a
   second build overwrites (not appends) — Linux only: Windows Spark has no winutils and cannot
   write local files, so that test skips there and runs in CI and in WSL.

dbt runs as a subprocess with cwd = the tmp project: profiles.yml's Spark paths (Derby,
warehouse dir) are RELATIVE to the process cwd, and dbt's target/ and logs/ follow the project
dir, so nothing lands in the repo. No network: every model is `select ... from values`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

ARTISTS = """{{ config(alias='artists') }}
select * from values (1, 'Radiohead', 2), (2, 'Björk', 1), (3, 'Daft Punk', 2)
    as artists(artist_id, artist_name, artist_type_id)
"""

ARTISTS_WITH_TYPES = """{{ config(alias='artists_with_types') }}
with artist_types as (
    select * from values (1, 'Person'), (2, 'Group') as artist_types(artist_type_id, artist_type_name)
)
select artists.artist_id, artists.artist_name, artist_types.artist_type_name
from {{ ref('cleansed_musicbrainz__artists') }} as artists
left join artist_types on artists.artist_type_id = artist_types.artist_type_id
"""

REF_ARTISTS = "{{ ref('cleansed_musicbrainz__artists') }}"


# dbt through THIS interpreter, by its console-script entry point (dbt_core's entry_points.txt:
# `dbt = dbt.cli.main:cli`). Not the `dbt` launcher: a venv's .exe launchers embed the path of the
# python they were generated for, which goes stale when the checkout moves; and `python -m dbt`
# does not exist. -X utf8 so Björk survives a cp1252 console.
DBT = [sys.executable, "-X", "utf8", "-c", "from dbt.cli.main import cli; cli()"]


@pytest.fixture
def dbt_project(tmp_path: Path) -> Path:
    """A copy of the repo's dbt project with an EMPTY models tree (the repo's models never run here)."""
    for name in ("dbt_project.yml", "profiles.yml"):
        shutil.copy(REPO_ROOT / name, tmp_path / name)
    shutil.copytree(REPO_ROOT / "macros", tmp_path / "macros")
    project = yaml.safe_load((REPO_ROOT / "dbt_project.yml").read_text(encoding="utf-8"))
    for layer, sources in project["models"]["audio_features"].items():
        if layer.startswith("+"):
            continue
        for source in sources:
            if not source.startswith("+"):
                (tmp_path / "models" / layer / source).mkdir(parents=True)
    return tmp_path


def write_model(project: Path, layer: str, source: str, name: str, sql: str) -> Path:
    path = project / "models" / layer / source / f"{name}.sql"
    path.write_text(sql, encoding="utf-8")
    return path


def run_dbt(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*DBT, "--no-use-colors", "--no-partial-parse", *args, "--target", "dev",
         "--project-dir", str(project), "--profiles-dir", str(project)],
        cwd=project, capture_output=True, text=True, encoding="utf-8",
    )


def test_two_models_with_one_bare_name_fail_parse(dbt_project: Path):
    write_model(dbt_project, "cleansed", "musicbrainz", "cleansed_musicbrainz__artists", ARTISTS)
    write_model(dbt_project, "staging", "musicbrainz", "cleansed_musicbrainz__artists", ARTISTS)
    result = run_dbt(dbt_project, "parse")
    assert result.returncode == 2, result.stdout + result.stderr
    assert 'dbt found two models with the name "cleansed_musicbrainz__artists"' in result.stdout


def test_aliased_model_compiles_to_bare_schema_dot_table(dbt_project: Path):
    write_model(dbt_project, "cleansed", "musicbrainz", "cleansed_musicbrainz__artists", ARTISTS)
    write_model(dbt_project, "staging", "musicbrainz", "staging_musicbrainz__artists_with_types",
                ARTISTS_WITH_TYPES)
    result = run_dbt(dbt_project, "compile", "--inline", f"select 1 from {REF_ARTISTS}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "select 1 from cleansed_musicbrainz.artists" in result.stdout
    assert "dev_cleansed_musicbrainz" not in result.stdout


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Spark cannot write local files on Windows without winutils; runs in CI (Linux) and "
    'in WSL via scripts/spark_wsl.ps1 -Run "pytest tests/test_dbt_project.py"',
)
def test_build_writes_bare_tables_under_layer_source_and_overwrites(dbt_project: Path):
    write_model(dbt_project, "cleansed", "musicbrainz", "cleansed_musicbrainz__artists", ARTISTS)
    write_model(dbt_project, "staging", "musicbrainz", "staging_musicbrainz__artists_with_types",
                ARTISTS_WITH_TYPES)
    first = run_dbt(dbt_project, "build")
    assert first.returncode == 0, first.stdout + first.stderr
    assert "PASS=2" in first.stdout

    # No data_root var, so dbt_project.yml's default <profiles dir>/data/<target>/ applies.
    data = dbt_project / "data" / "dev"
    for layer, table in (("cleansed", "artists"), ("staging", "artists_with_types")):
        parts = list((data / layer / "musicbrainz" / table).glob("part-*.parquet"))
        assert parts, f"no Parquet under data/dev/{layer}/musicbrainz/{table}/"
    assert not (data / "cleansed_musicbrainz").exists()
    assert not (data / "spark-warehouse" / "cleansed_musicbrainz.db" / "artists").exists()

    # The table materialization drops and re-creates over a non-empty external location:
    # allowNonEmptyLocationInCTAS makes that an overwrite, and the row count proves it.
    second = run_dbt(dbt_project, "build")
    assert second.returncode == 0, second.stdout + second.stderr
    shown = run_dbt(dbt_project, "show", "--inline",
                    f"select count(*) as artist_count from {REF_ARTISTS}")
    assert shown.returncode == 0, shown.stdout + shown.stderr
    assert re.search(r"\|\s*3\s*\|", shown.stdout), shown.stdout

    # The data_root var is the seam task_4's synthetic-build test will use: a build pointed
    # elsewhere lands there, under the same <layer>/<source>/<alias> path, and not under data/.
    custom_root = dbt_project / "custom_root"
    moved = run_dbt(dbt_project, "build", "--vars", json.dumps({"data_root": str(custom_root)}))
    assert moved.returncode == 0, moved.stdout + moved.stderr
    assert list((custom_root / "cleansed" / "musicbrainz" / "artists").glob("part-*.parquet"))
    assert list((custom_root / "staging" / "musicbrainz" / "artists_with_types").glob("part-*.parquet"))
    assert not (custom_root / "data").exists()
