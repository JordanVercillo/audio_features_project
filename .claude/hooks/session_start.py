# /// script
# requires-python = ">=3.10"
# ///
"""
SessionStart hook (harness kit): every session starts warm. Emits, as additionalContext,
the RESUME block of notes/PROJECT_CONTEXT.md (the lines between its "RESUME HERE" heading and the
first ---, capped at RESUME_CAP lines), the branch and tree state, how far the branch is behind its
upstream and origin/main (counted against the last fetch, which it dates; the hook never fetches,
so it costs no network and can't hang on one), every open session brief /resume wrote (newest
first; a pack saved beside a brief, *.pack_*.md, is never one), and the newest handoff written by
/handoff, if any. Briefs and handoffs live in the main checkout's project-data folder, also for a
session in a worktree.

Facts only, no imperatives: the hook docs warn that system-style phrasing can trip
prompt-injection defences. The whole body runs under one try/except: any failure emits nothing
and exits 0, so the hook can never block a session or print a traceback into it.

Registered in .claude/settings.json (an absolute $CLAUDE_PROJECT_DIR path; `python` in place of
`uv run` where uv is absent):
  "SessionStart": [{"matcher": "startup|resume|clear|compact",
                    "hooks": [{"type": "command",
                               "command": "uv run \\"$CLAUDE_PROJECT_DIR/.claude/hooks/session_start.py\\""}]}]
"""
import datetime
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RESUME_CAP = 40  # lines of the RESUME block injected at most; the budget is 20, so a hit here is a finding
PACK = "*.pack_*.md"  # a sitting's pack, saved beside its brief as evidence: never a brief


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                              timeout=10, encoding="utf-8", errors="replace").stdout.strip()
    except Exception:
        return ""





def resume_block(root: Path) -> str:
    p = root / "notes" / "PROJECT_CONTEXT.md"
    if not p.exists():
        return ""
    out, inside = [], False
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## ") and "RESUME HERE" in line:
            inside = True
            continue
        if inside and line.strip() == "---":
            break
        if inside:
            out.append(line)
    if len(out) > RESUME_CAP:
        total = len(out)
        out = out[:RESUME_CAP] + [f"(... {total - RESUME_CAP} more lines not shown: the RESUME block is {total} lines "
                                 f"against a 20-line budget, so /wrap-session should condense it.)"]
    return "\n".join(out).strip()


def project_key(root: Path) -> str:
    # Claude Code names a project's data folder after its path, every character that isn't a letter
    # or a digit made '-': C:\Users\x\my_repo -> C--Users-x-my-repo
    return re.sub(r"[^A-Za-z0-9]", "-", str(root.resolve()))


def main_checkout(root: Path) -> Path:
    # A worktree's git common dir is the main checkout's .git; /resume and /handoff write under the
    # main checkout's project-data folder, so a worktree session looks there too.
    common = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).parent if common else root


def data_folder(root: Path) -> Path:
    return Path.home() / ".claude" / "projects" / project_key(main_checkout(root))


def open_md(folder: Path) -> list[str]:
    # Every *.md directly in `folder`, newest first: a closed\ subfolder isn't read, and a pack saved
    # beside a brief (PACK) is skipped however new it is. [] when there is none.
    if not folder.is_dir():
        return []
    files = [f for f in folder.glob("*.md") if not fnmatch.fnmatch(f.name, PACK)]
    return [str(f) for f in sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)]


def brief_fact(briefs: list[str]) -> str:
    if not briefs:
        return ""
    if len(briefs) == 1:
        return (f"An open session brief exists at {briefs[0]} (written by /resume; a brief stays open "
                "until /wrap-session moves it to closed\\, so its session never wrapped or is still running).")
    return (f"{len(briefs)} open session briefs exist (written by /resume; a brief stays open until "
            "/wrap-session moves it to closed\\, so each one's session never wrapped or is still running), "
            "newest first:\n" + "\n".join(briefs))


def behind(root: Path, upstream: str) -> str:
    # How far HEAD is behind its upstream and origin/main, counted against the remote refs as the
    # last fetch left them, with that fetch's date (FETCH_HEAD's newest copy).
    refs = [r for r in dict.fromkeys([upstream, "origin/main"]) if r and git(root, "rev-parse", "--verify", "-q", r)]
    if not refs:
        return ""
    counts = "; ".join(f"behind {r}: {git(root, 'rev-list', '--count', f'HEAD..{r}') or '?'}" for r in refs)
    heads = {git(root, "rev-parse", "--path-format=absolute", "--git-path", "FETCH_HEAD"),
             str(Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir") or ".") / "FETCH_HEAD")}
    times = [Path(h).stat().st_mtime for h in heads if h and Path(h).is_file()]
    when = (f"the last fetch, {datetime.datetime.fromtimestamp(max(times)):%Y-%m-%d %H:%M}" if times
            else "the remote refs; no fetch is recorded")
    return f"{counts} (counted against {when})"


def build_context() -> str:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    
    parts = []
    block = resume_block(root)
    if block:
        parts.append("notes/PROJECT_CONTEXT.md, RESUME HERE block:\n" + block)
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if branch:
        dirty = git(root, "status", "--porcelain")
        upstream = git(root, "rev-parse", "--abbrev-ref", "@{upstream}")
        ahead = git(root, "rev-list", "--count", "@{upstream}..HEAD") if upstream else "no upstream"
        n_dirty = len(dirty.splitlines()) if dirty else 0
        lag = behind(root, upstream)
        parts.append(f"git: branch {branch}; {n_dirty} uncommitted path(s); unpushed commits: {ahead}"
                     + (f"; {lag}." if lag else "."))
    fact = brief_fact(open_md(data_folder(root) / "sessions"))
    if fact:
        parts.append(fact)
    handoffs = open_md(data_folder(root) / "handoffs")
    if handoffs:
        parts.append(f"A handoff document from an earlier session exists at {handoffs[0]} "
                     "(written by /handoff; /resume reads it).")
    return "\n\n".join(parts)


def main() -> int:
    try:
        context = build_context()
        if context:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                     "additionalContext": context}}))
    except Exception:
        pass  # a warm start is a convenience; a traceback at session start is not
    return 0


if __name__ == "__main__":
    sys.exit(main())
