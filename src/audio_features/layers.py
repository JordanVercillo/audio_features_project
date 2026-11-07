"""layers — the warehouse's environments, layers and on-disk paths, as facts.

The local mirror of project.layer_source.table (spec: naming_and_layout):
  environment   dev | prd — a dbt target and a data root, data/<environment>/
  layer         the five, in pipeline order: ingest, cleansed, staging, modeled, report
  source        the dbt schema is <layer>_<source> (cleansed_musicbrainz, modeled_music)
  on disk       data/<environment>/<layer>/<source>/<table>/

No I/O: nothing here touches the filesystem or the network, so the audit's tests can import
it and a wrong path is a ValueError, never a missing directory found at build time.

LAYERS is duplicated, deliberately, in .claude/skills/warehouse-audit/audit_warehouse.py: the
audit runs as a `sys.executable -I` script and cannot import this package, so "shared" means a
test asserts the two literals agree. Keep both plain literals.
"""
from __future__ import annotations

from pathlib import Path

ENVIRONMENTS = ("dev", "prd")
LAYERS = ("ingest", "cleansed", "staging", "modeled", "report")

# src/audio_features/layers.py -> the repo root is three parents up.
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"


def _check(kind: str, value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"unknown {kind} {value!r}; expected one of {', '.join(allowed)}")


def environment_root(environment: str, data_root: Path | None = None) -> Path:
    """data/<environment>/ — the data root a dbt target builds into."""
    _check("environment", environment, ENVIRONMENTS)
    return (data_root or DATA_ROOT) / environment


def layer_path(
    environment: str,
    layer: str,
    source: str,
    table: str | None = None,
    data_root: Path | None = None,
) -> Path:
    """data/<environment>/<layer>/<source>[/<table>] — a source folder, or one table under it."""
    _check("layer", layer, LAYERS)
    path = environment_root(environment, data_root) / layer / source
    return path / table if table else path


def schema_name(layer: str, source: str) -> str:
    """The dbt schema for a layer and source: `<layer>_<source>` (cleansed_musicbrainz)."""
    _check("layer", layer, LAYERS)
    return f"{layer}_{source}"
