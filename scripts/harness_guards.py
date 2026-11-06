# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""harness_guards — the Claude Code harness's own hygiene rules, as facts.

Portable: reads only .claude/, CLAUDE.md and notes/PROJECT_CONTEXT.md. Install as
scripts/harness_guards.py and run it in CI and before every commit that touches the harness.

Checks (each reports ok + findings):
  skill_frontmatter  every .claude/skills/<name>/SKILL.md has strict YAML frontmatter (no duplicate
                     keys), name equal to its folder and a non-empty description, so Claude Code
                     can load it
  agent_roster       every .claude/agents/<name>.md has strict YAML frontmatter with name equal to
                     its file stem and a description; is named in CLAUDE.md; every path under
                     `## Your files` exists; no path under `## Creates at first task` exists yet
  rules_frontmatter  every .claude/rules/**/*.md either has no frontmatter or a `paths:` block that
                     parses (a block that doesn't parse loads the rule unscoped with no error)
  hooks_registered   every .claude/hooks/* script is referenced by a command in
                     .claude/settings.json, and every hook command that names a file under
                     .claude/hooks/ names one that exists
  memory_budget      notes/PROJECT_CONTEXT.md stays within budget: <= --context-lines lines
                     (150), a RESUME HERE block of <= --resume-lines (20), <= --log-entries dated
                     Session log entries (10)

Usage:  uv run scripts/harness_guards.py [--root DIR] [--skip CHECK ...] [--context-lines N]
                                         [--resume-lines N] [--log-entries N]
Emits one JSON object; exits 0 when every check that ran passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
while ROOT != ROOT.parent and not (ROOT / ".claude").is_dir():
    ROOT = ROOT.parent
sys.dont_write_bytecode = True

LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
LOG_ENTRY = re.compile(r"^- \*\*\d{4}-\d{2}-\d{2}\*\*")


class StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys (PyYAML keeps the last one silently)."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise yaml.constructor.ConstructorError(None, None, f"duplicate key {key!r}", key_node.start_mark)
            seen.add(key)
        return super().construct_mapping(node, deep)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """(frontmatter text or None, body). Frontmatter is the block between a leading --- line and the
    next --- line."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return "\n".join(lines[1:]), ""


def frontmatter_findings(rel: str, text: str, expected_name: str, kind: str, what: str) -> tuple[list[str], dict]:
    fm_text, _ = split_frontmatter(text)
    if fm_text is None:
        return [f"{rel}: no frontmatter, so Claude Code won't load this {kind}"], {}
    try:
        fm = yaml.load(fm_text, Loader=StrictLoader)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" at frontmatter line {mark.line + 1}" if mark else ""
        return [f"{rel}: frontmatter isn't valid YAML{where} ({getattr(e, 'problem', e)}); an unquoted ': ' inside a value is the usual cause, so quote the value"], {}
    if not isinstance(fm, dict):
        return [f"{rel}: frontmatter isn't a mapping"], {}
    findings = []
    if fm.get("name") != expected_name:
        findings.append(f"{rel}: name {fm.get('name')!r} must equal its {what} {expected_name!r}")
    if not str(fm.get("description") or "").strip():
        findings.append(f"{rel}: description is missing or empty")
    return findings, fm


def md_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current, fenced = None, False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif fenced:
            continue
        elif line.startswith("## "):
            current = line[3:].strip().rstrip(":").strip().lower()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return sections


def claimed_paths(lines: list[str]) -> list[str]:
    paths = []
    for line in lines:
        m = LIST_ITEM.match(line)
        if m is None:
            continue
        body = m.group(1).strip()
        if body.lower().startswith("none"):
            continue
        tokens = re.findall(r"`([^`]+)`", body)
        if tokens:
            paths.append(tokens[0].strip())
    return paths


def check_skill_frontmatter() -> list[str]:
    findings = []
    for sm in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        rel = sm.relative_to(ROOT).as_posix()
        f, _ = frontmatter_findings(rel, read(sm), sm.parent.name, "skill", "folder name")
        findings += f
    return findings


def check_agent_roster() -> list[str]:
    findings = []
    claude_md = read(ROOT / "CLAUDE.md") if (ROOT / "CLAUDE.md").exists() else ""
    for am in sorted((ROOT / ".claude" / "agents").glob("*.md")):
        if am.name.upper().startswith("_") or am.name.endswith(".TEMPLATE.md"):
            continue
        rel = am.relative_to(ROOT).as_posix()
        text = read(am)
        f, fm = frontmatter_findings(rel, text, am.stem, "seat", "file name")
        findings += f
        if fm and f"`{am.stem}`" not in claude_md and am.stem not in claude_md:
            findings.append(f"{rel}: seat {am.stem!r} isn't named in CLAUDE.md (add it to the roster)")
        sections = md_sections(text)
        for p in claimed_paths(sections.get("your files", [])):
            if not (ROOT / p.rstrip("/")).exists():
                findings.append(f"{rel} Your files: `{p}` doesn't exist (move it to '## Creates at first task' until it does)")
        for p in claimed_paths(sections.get("creates at first task", [])):
            if (ROOT / p.rstrip("/")).exists():
                findings.append(f"{rel} Creates at first task: `{p}` already exists (move it to '## Your files')")
    return findings


def check_rules_frontmatter() -> list[str]:
    findings = []
    rules = ROOT / ".claude" / "rules"
    if not rules.is_dir():
        return findings
    for rm in sorted(rules.rglob("*.md")):
        rel = rm.relative_to(ROOT).as_posix()
        fm_text, _ = split_frontmatter(read(rm))
        if fm_text is None:
            continue
        try:
            fm = yaml.load(fm_text, Loader=StrictLoader)
        except yaml.YAMLError as e:
            findings.append(f"{rel}: frontmatter isn't valid YAML ({getattr(e, 'problem', e)}); Claude Code would load this rule unscoped")
            continue
        paths = (fm or {}).get("paths")
        if paths is None:
            findings.append(f"{rel}: frontmatter has no `paths:`; drop the frontmatter or scope the rule")
        elif not (isinstance(paths, str) or (isinstance(paths, list) and all(isinstance(x, str) for x in paths))):
            findings.append(f"{rel}: `paths:` must be a string or a list of strings")
    return findings


def check_hooks_registered() -> list[str]:
    findings = []
    hooks_dir = ROOT / ".claude" / "hooks"
    settings = ROOT / ".claude" / "settings.json"
    commands: list[str] = []
    if settings.exists():
        try:
            cfg = json.loads(read(settings))
        except json.JSONDecodeError as e:
            return [f".claude/settings.json: not valid JSON ({e})"]
        for _event, entries in (cfg.get("hooks") or {}).items():
            for entry in entries:
                for h in entry.get("hooks", []):
                    if h.get("type") == "command":
                        commands.append(h.get("command", ""))
    for cmd in commands:
        for m in re.finditer(r"\.claude/hooks/([\w.\-]+)", cmd):
            if not (hooks_dir / m.group(1)).exists():
                findings.append(f".claude/settings.json: hook command names .claude/hooks/{m.group(1)}, which doesn't exist")
    if hooks_dir.is_dir():
        for script in sorted(hooks_dir.iterdir()):
            if script.is_file() and not any(script.name in c for c in commands):
                findings.append(f".claude/hooks/{script.name}: not registered in .claude/settings.json (dead hook, or missing registration)")
    return findings


def check_memory_budget(context_lines: int, resume_lines: int, log_entries: int) -> list[str]:
    p = ROOT / "notes" / "PROJECT_CONTEXT.md"
    if not p.exists():
        return ["notes/PROJECT_CONTEXT.md: missing"]
    lines = read(p).splitlines()
    findings = []
    if len(lines) > context_lines:
        findings.append(f"notes/PROJECT_CONTEXT.md: {len(lines)} lines, budget {context_lines} (condense; history lives in git)")
    resume, inside, seen = 0, False, False
    for line in lines:
        if line.startswith("## ") and "RESUME HERE" in line:
            inside, seen = True, True
            continue
        if inside and line.strip() == "---":
            break
        if inside:
            resume += 1
    if not seen:
        findings.append("notes/PROJECT_CONTEXT.md: no '## ⏭️ RESUME HERE' heading")
    elif resume > resume_lines:
        findings.append(f"notes/PROJECT_CONTEXT.md: RESUME HERE block is {resume} lines, budget {resume_lines}")
    entries = sum(1 for line in lines if LOG_ENTRY.match(line))
    if entries > log_entries:
        findings.append(f"notes/PROJECT_CONTEXT.md: {entries} Session log entries, budget {log_entries}")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip", nargs="*", default=[], help="checks to skip")
    ap.add_argument("--context-lines", type=int, default=150)
    ap.add_argument("--resume-lines", type=int, default=20)
    ap.add_argument("--log-entries", type=int, default=10)
    ap.add_argument("--root", help="repo root (default: the nearest ancestor of this script with a .claude/)")
    a = ap.parse_args()
    global ROOT
    if a.root:
        ROOT = Path(a.root).resolve()
    checks = {
        "skill_frontmatter": check_skill_frontmatter,
        "agent_roster": check_agent_roster,
        "rules_frontmatter": check_rules_frontmatter,
        "hooks_registered": check_hooks_registered,
        "memory_budget": lambda: check_memory_budget(a.context_lines, a.resume_lines, a.log_entries),
    }
    out = {"root": str(ROOT), "ok": True, "checks": {}}
    for name, fn in checks.items():
        if name in a.skip:
            out["checks"][name] = {"ok": None, "findings": ["skipped"]}
            continue
        findings = fn()
        out["checks"][name] = {"ok": not findings, "findings": findings}
        out["ok"] = out["ok"] and not findings
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
