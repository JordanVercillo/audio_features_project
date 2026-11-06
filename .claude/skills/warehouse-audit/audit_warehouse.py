# /// script
# requires-python = ">=3.11"
# dependencies = ["pyarrow>=14"]
# ///
"""audit_warehouse — facts about the audio_features warehouse, as one JSON object. Judgment stays in the skill.

Contract:
  {"inventory": {...}, "errors": [...], "warnings": [...],
   "flags": {"NO_DATA", "DUMP_STALE", "NO_MANIFEST", "LAYER_MISSING", "LAYER_PARITY"}}

- errors   block the work they touch (the partner skill fixes or descopes first)
- warnings resize the work
- flags    are branch points the partner skill reads; every flag is listed in the skill's "Flag meanings"
- exit 0 even with findings (the report IS the result); exit 1 only when the audit itself can't run
- absent data is a flag (NO_DATA), never a crash

Layout audited: data/<layer>/<table>/*.parquet (or data/<layer>/<table>.parquet), layers in order
ingest, cleansed, staging, modeled, report. The ingest writes data/ingest/_manifest.json with at
least {"dump": "<YYYYMMDD-HHMMSS>"}; the audit compares it to the one-line LATEST file at the
MusicBrainz fullexport URL (16 bytes, 10 s timeout; unreachable is a warning, never a crash).

Usage:  uv run .claude/skills/warehouse-audit/audit_warehouse.py [--root DIR] [--offline]
                                                                   [--parity-threshold 0.2] [--json-indent N]
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import urllib.request
from pathlib import Path

LAYERS = ["ingest", "cleansed", "staging", "modeled", "report"]
LATEST_URL = "https://data.metabrainz.org/pub/musicbrainz/data/fullexport/LATEST"


def table_rows(path: Path) -> int | None:
    """Row count from Parquet metadata (no full read); None when pyarrow is unavailable."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return None
    files = [path] if path.is_file() else sorted(path.glob("*.parquet"))
    return sum(pq.ParquetFile(f).metadata.num_rows for f in files)


def check_layers(root: Path, report: dict, opts: argparse.Namespace) -> None:
    """Which layers and tables exist, with row counts; NO_DATA when none; LAYER_MISSING when out of order."""
    data = root / "data"
    layers: dict[str, dict] = {}
    for layer in LAYERS:
        d = data / layer
        if not d.is_dir():
            continue
        tables = {}
        for t in sorted(d.iterdir()):
            if t.name.startswith("_"):
                continue
            if t.is_dir() or t.suffix == ".parquet":
                tables[t.stem if t.is_file() else t.name] = table_rows(t)
        layers[layer] = {"tables": tables, "rows": sum(r for r in tables.values() if r is not None)}
    report["inventory"]["layers"] = layers
    report["inventory"]["layers_present"] = len(layers)
    report["inventory"]["tables"] = sum(len(v["tables"]) for v in layers.values())
    report["inventory"]["rows"] = sum(v["rows"] for v in layers.values())
    if not layers:
        report["flags"]["NO_DATA"] = True
        report["warnings"].append(f"nothing to audit yet: no layer folder under {data}")
        return
    if any(r is None for v in layers.values() for r in v["tables"].values()):
        report["warnings"].append("pyarrow not importable: row counts unavailable (run through `uv run`)")
    present = [layer for layer in LAYERS if layer in layers]
    for i, layer in enumerate(LAYERS):
        if layer in layers:
            continue
        later = [x for x in present if LAYERS.index(x) > i]
        if later:
            report["flags"]["LAYER_MISSING"] = True
            report["errors"].append(f"layer {layer!r} is absent while {later} exist: layers are rebuilt in order")


def check_freshness(root: Path, report: dict, opts: argparse.Namespace) -> None:
    """The loaded dump vs LATEST on data.metabrainz.org."""
    if report["flags"]["NO_DATA"] or "ingest" not in report["inventory"]["layers"]:
        report["inventory"]["dump"] = None
        return
    manifest = root / "data" / "ingest" / "_manifest.json"
    if not manifest.is_file():
        report["inventory"]["dump"] = None
        report["flags"]["NO_MANIFEST"] = True
        report["warnings"].append(f"{manifest} is absent: the ingest never recorded which dump it loaded")
        return
    try:
        dump = str(json.loads(manifest.read_text(encoding="utf-8")).get("dump") or "")
    except (json.JSONDecodeError, OSError) as exc:
        dump = ""
        report["warnings"].append(f"{manifest} unreadable: {exc}")
    report["inventory"]["dump"] = dump or None
    if opts.offline:
        report["inventory"]["latest"] = "skipped"
        return
    try:
        with urllib.request.urlopen(LATEST_URL, timeout=10) as r:  # a fixed https URL, 16 bytes
            latest = r.read(64).decode("ascii", "replace").strip()
    except Exception as exc:  # network is a warning, never a crash
        report["inventory"]["latest"] = "unreachable"
        report["warnings"].append(f"LATEST unreachable ({type(exc).__name__}); freshness not judged")
        return
    report["inventory"]["latest"] = latest
    if dump and dump != latest:
        report["flags"]["DUMP_STALE"] = True
        report["warnings"].append(f"loaded dump {dump} is not LATEST {latest}: the weekly refresh is due")


def check_parity(root: Path, report: dict, opts: argparse.Namespace) -> None:
    """A table's row count must not drop by more than the threshold between adjacent layers."""
    layers = report["inventory"]["layers"]
    present = [layer for layer in LAYERS if layer in layers]
    drops = []
    checked = 0
    for lo, hi in itertools.pairwise(present):
        for table, n_lo in layers[lo]["tables"].items():
            n_hi = layers[hi]["tables"].get(table)
            if n_hi is None:
                continue
            checked += 1
            if n_lo in (None, 0):
                continue
            drop = 1 - n_hi / n_lo
            if drop > opts.parity_threshold:
                drops.append(f"{table}: {lo} {n_lo} -> {hi} {n_hi} ({drop:.0%} drop > {opts.parity_threshold:.0%})")
    report["inventory"]["parity_checked"] = checked
    if drops:
        report["flags"]["LAYER_PARITY"] = True
        report["errors"].extend("parity: " + d for d in drops)


CHECKS = [check_layers, check_freshness, check_parity]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--offline", action="store_true", help="skip the LATEST lookup (CI, no network)")
    ap.add_argument("--parity-threshold", type=float, default=0.2)
    ap.add_argument("--json-indent", type=int, default=2)
    a = ap.parse_args()
    report = {"inventory": {}, "errors": [], "warnings": [],
              "flags": {"NO_DATA": False, "DUMP_STALE": False, "NO_MANIFEST": False,
                        "LAYER_MISSING": False, "LAYER_PARITY": False}}
    try:
        for check in CHECKS:
            check(a.root.resolve(), report, a)
    except Exception as exc:  # the audit itself failed: say so, exit 1
        print(json.dumps({"audit_error": f"{type(exc).__name__}: {exc}"}))
        return 1
    print(json.dumps(report, indent=a.json_indent, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
