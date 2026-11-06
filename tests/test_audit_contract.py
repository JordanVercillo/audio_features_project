"""The warehouse audit keeps its JSON contract and is graceful when data is absent (no network)."""
import json
import subprocess
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "warehouse-audit" / "audit_warehouse.py"


def run_audit(root: Path) -> dict:
    out = subprocess.run([sys.executable, "-I", str(AUDIT), "--root", str(root), "--offline"],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_absent_data_is_a_flag_not_a_crash(tmp_path: Path):
    report = run_audit(tmp_path)
    assert set(report) == {"inventory", "errors", "warnings", "flags"}
    assert report["flags"]["NO_DATA"] is True
    assert report["errors"] == []


def test_layer_out_of_order_is_an_error(tmp_path: Path):
    (tmp_path / "data" / "staging" / "artist").mkdir(parents=True)
    report = run_audit(tmp_path)
    assert report["flags"]["LAYER_MISSING"] is True
    assert any("cleansed" in e for e in report["errors"])


def test_parity_drop_is_flagged(tmp_path: Path):
    pa = __import__("pytest").importorskip("pyarrow")
    pq = __import__("pyarrow.parquet").parquet
    for layer, n in (("ingest", 100), ("cleansed", 50)):
        d = tmp_path / "data" / layer / "artist"
        d.mkdir(parents=True)
        pq.write_table(pa.table({"id": list(range(n))}), d / "part-0.parquet")
    report = run_audit(tmp_path)
    assert report["flags"]["LAYER_PARITY"] is True
    assert report["inventory"]["layers"]["ingest"]["tables"]["artist"] == 100
