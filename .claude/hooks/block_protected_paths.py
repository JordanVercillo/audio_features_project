# /// script
# requires-python = ">=3.10"
# ///
"""
PreToolUse hook: hard-block Edit/Write to paths the house rules protect. Turns a CLAUDE.md
"never hand-edit X" rule from prose into a machine gate.

Contract: reads the hook JSON on stdin; exit 2 blocks the tool call with the stderr message shown
to the agent; exit 0 allows. Never blocks reads. Malformed input never bricks the harness.
Register in .claude/settings.json with an absolute $CLAUDE_PROJECT_DIR path: a relative path breaks
the moment the shell's working directory moves.

Fill PROTECTED with this repo's paths (lower-case, forward slashes, relative to the repo root; a
folder entry ends in "/" and matches at a folder boundary, so "data/" catches data/x.csv and
src/data/x.csv but never AppData/; a file entry such as "docs/index.md" matches that exact path) and
PROTECTED_SUFFIXES with file kinds only a tool should write. Typical entries: vendor folders,
generated files (an index, a catalog, a view), a read-only synced copy, binary payloads.
"""
import json
import os
import re
import sys

PROTECTED = (
    ("data/",            "rebuildable data: dumps and Parquet layers are written by the pipeline, never by hand (CLAUDE.md rule 2)"),
    (".venv/",           "the uv-managed environment; change pyproject.toml and run `uv sync`"),
    ("spark-warehouse/", "Spark's own output; rebuilt by dbt"),
    ("metastore_db/",    "Spark's Derby metastore; never hand-edited"),
)
PROTECTED_SUFFIXES = (
    (".lock",            "lock files are written by the package manager (`uv lock`)"),
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get("tool_name") not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return 0
    raw = (payload.get("tool_input") or {}).get("file_path") or ""
    p = raw.replace("\\", "/").lower()
    # Match inside the repo, not the machine: a path under the project dir is compared relative to
    # it, anchored at a folder boundary, so protecting "data/" never catches "AppData/Local/...".
    root = (os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()).replace("\\", "/").lower().rstrip("/")
    if root and p.startswith(root + "/"):
        p = p[len(root) + 1:]
    elif p.startswith("/") or re.match(r"^[a-z]:/", p):
        return 0  # an absolute path outside this repo: its house rules don't apply there
    for frag, why in PROTECTED:
        hit = (p.startswith(frag) or f"/{frag}" in p) if frag.endswith("/") else p == frag
        if hit:
            print(f"BLOCKED by .claude/hooks/block_protected_paths.py: '{raw}' is protected ({why}). "
                  f"If this edit is genuinely required, the owner lifts the block explicitly.", file=sys.stderr)
            return 2
    for suf, why in PROTECTED_SUFFIXES:
        if p.endswith(suf):
            print(f"BLOCKED by .claude/hooks/block_protected_paths.py: '{raw}' ({why}). "
                  f"If this edit is genuinely required, the owner lifts the block explicitly.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
