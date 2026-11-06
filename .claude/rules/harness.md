---
paths:
  - ".claude/**"
---
# Writing seats, skills, hooks and rules (loads only while editing `.claude/`)

- A skill's `description` is its always-loaded pointer: trigger words first, one trigger per branch, nothing the body repeats. A skill only the owner should start gets `disable-model-invocation: true`; it then can't be called by another skill, so what `/orchestrator` and `/ship` call (`/verify`, `/ship`, `/spec`, `/interview-me`, where installed) stays model-invocable, and `/retro` for `/wrap-session`.
- Every step ends in a completion criterion the agent can check. State the target behaviour; a prohibition stands only as a hard guardrail, paired with the positive form.
- One home per fact: link the doc that owns a rule, never paste from it. A rule file here is a pointer plus the three to five lines that must sit in front of the agent while it edits matching files.
- A seat lists `## Your files` (each must exist) and `## Creates at first task` (none may yet), and is in the CLAUDE.md roster; a skill's `name` equals its folder. Strict YAML. `uv run scripts/harness_guards.py` checks it. A rule whose `paths:` YAML doesn't parse loads unscoped with no error, so check it by hand.
- The skills under `.claude/skills/` are this repo's adapted copies from the harness kit: improve a copy here for this repo; carry a generic improvement back to the kit without this repo's specifics.
- A new skill or seat gets its routing row in `CLAUDE.md`. A line nobody acted on all session is a deletion candidate (`/retro`).
- Hooks are PEP 723 scripts run by `uv run` from an absolute `$CLAUDE_PROJECT_DIR` path; malformed input never blocks (exit 0); a block is exit 2 with the reason on stderr.
