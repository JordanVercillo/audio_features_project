# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Validate an implementation spec — makes "is this a well-formed spec?" a fact,
not a judgment (CLAUDE.md rule 5: facts by script).

Checks the required top-level sections exist and are non-empty, warns on the
recommended ones, and emits ONE JSON object:
    {valid, missing_sections, warnings, present_sections}
Exit 0 when valid, 1 when a required section is missing/empty, 2 on bad usage.

Run: uv run .claude/skills/spec/validate_spec.py specs/<name>_spec.yaml
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

# The contract every spec must satisfy (mirrors language-models' generate-spec).
REQUIRED = ["approach", "tasks", "integration_steps", "evaluation_plan",
            "reference_materials", "verification"]
RECOMMENDED = ["success_criteria"]
_EMPTY = (None, "", [], {})


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"valid": False, "error": "usage: validate_spec.py <spec.yaml>"}))
        return 2
    path = Path(sys.argv[1]).expanduser()
    if not path.is_file():
        print(json.dumps({"valid": False, "error": f"not found: {path}"}))
        return 2
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        print(json.dumps({"valid": False, "error": f"YAML parse error: {exc}"}))
        return 1
    if not isinstance(data, dict):
        print(json.dumps({"valid": False, "error": "top level is not a mapping"}))
        return 1

    present = [k for k, v in data.items() if v not in _EMPTY]
    missing = [s for s in REQUIRED if s not in present]
    warnings = [f"missing recommended section: {s}" for s in RECOMMENDED if s not in present]
    # verification must carry at least one runnable check to be worth anything.
    if "verification" in present and not data.get("verification"):
        warnings.append("verification is empty — give at least one runnable check")

    valid = not missing
    print(json.dumps({
        "valid": valid,
        "missing_sections": missing,
        "warnings": warnings,
        "present_sections": present,
    }, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
