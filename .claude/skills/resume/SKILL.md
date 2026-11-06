---
name: resume
description: Start a session warm — orient from the repo's living memory, check its health, write the session brief, hand it to /orchestrator. TRIGGER when the user types /resume, "pick up where we left off", "get me back up to speed", or starts a session cold. SKIP for a specific new task that states its own goal (/orchestrator writes the brief then).
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash, PowerShell, Write, Skill]
---

Get oriented from the repo's own memory, prove the state, spec the session, then start it. Run
the steps in order, in one turn. The turn ends with `/orchestrator` running on a written brief,
never with a question the repo could have answered. This copy is the repo's own. Its instruments: `uv run scripts/harness_guards.py`, `uv run .claude/skills/warehouse-audit/audit_warehouse.py` (dump freshness, layer presence, parity), `uv run ruff check .`; the tracker is GitHub issues and PRs via `gh`.

## 1 — Recall (read the memory; don't re-derive it)

- **Sync first.** `git fetch origin`. On `main`, `git pull --ff-only`; on another branch,
  `git fetch origin main:main`, and read the memory from `origin/main:notes/PROJECT_CONTEXT.md`
  when the branch's copy is older. Other sessions, cloud ones included, merge while this one is
  closed, and a stale memory file is wrong memory.
- Read `CLAUDE.md` (ground rules, routing, map), `notes/PROJECT_CONTEXT.md` in full,
  `notes/roadmap.md` (find the 📍), and the last 2–3 entries of `notes/journal.md`.
- **Continuations outrank the ➡️ NEXT ACTION**, in this order. Two kinds live in this repo's
  Claude Code project data folder, `~/.claude/projects/<project-key>/`, where `<project-key>` is
  the repo's absolute path with every character that isn't a letter or a digit made `-`
  (`/handoff` §1 says the same, with the worktree case):
  - first, a `/handoff` document in `handoffs/` (the SessionStart hook names the newest): its
    **Next step** comes before everything else until that task is done or wrapped;
  - then an open **session brief** in `sessions/` (not under `closed/`): the session that wrote
    it never wrapped, so its unticked **Done when** items and open items are this session's
    first candidates.
- **Unmerged memory.** `git branch -r --no-merged origin/main`: a `wrap/*` or `claude/*` branch
  that touches `notes/` is a wrap another session couldn't land (a cloud session can't commit to
  `main`). Read its session-log line and journal entry now; `/wrap-session` folds them into the
  memory and deletes the branch once the fold is pushed. Memory counts only once it is on `main`
  or on a PR that will get there.

## 2 — Health check (fast, deterministic)

- **The repo's deterministic checks**, the fast ones: the harness guards where the repo has them
  (`uv run scripts/harness_guards.py`, or the equivalent its `CLAUDE.md` names) and whatever lint
  or audit `CLAUDE.md` names. Report only the result. Don't run the full test suite or a build
  just to orient; if the repo keeps a verify verdict file, read it and say how fresh it is.
- `git status -sb` + `git log origin/main..HEAD --oneline`: uncommitted work, unpushed commits,
  and stray files at the repo root (a guard's output, a screenshot): each is a tidy item for the
  wrap, named now.
- `gh pr list --state open` and `gh run list --limit 3`: open PRs and red CI.
- `gh pr list --state merged --limit 10`: what landed since the latest session-log line. The
  memory may not know it yet.
- **The open items, live from the issue tracker:** `gh issue list --state open`, filtered the way
  the repo labels its work (the 📍 phase's milestone; a label for decisions waiting on the owner;
  a label for untriaged intakes). **The open-items ledger is derived here, every session, from the
  tracker and the checks; it is never stored in a file** (one home per fact). Issues the owner has
  marked as their own lane (a `dnd` label or its equivalent) are listed as DND only: never offered
  as work, never triaged, never counted as decisions waiting.
- A repo without an issue tracker: the open items are the 📍 phase's unticked roadmap items, and
  the brief says so.

## 3 — Emit the RESUME BRIEF

```
=== RESUME BRIEF ===
Repo:     <one line: what this is>
Where:    <roadmap phase + 📍 item>
Health:   <each deterministic check and its result, or "n/a">
Flags:    <behind origin / uncommitted / unpushed / stray files / open PRs / red CI / unmerged wrap branch, or "none">
Landed:   <PRs merged since the last session-log line, or "nothing new">
Left off: <the latest dated session-log line>
➡️ NEXT:  <PROJECT_CONTEXT's ➡️ NEXT ACTION verbatim>
Open:     <open items as #n title, grouped: blocks the next lane / doesn't>
DND:      <the owner's own lanes (hands off), or "none">
Owner:    <decisions waiting on the owner: merges, approvals, triages, rulings>
```

**Never end the turn on the brief.** It's orientation, not a deliverable.

## 4 — Spec this session: write the session brief

Pick the lane: the continuation from step 1 if there is one; otherwise the first item of the
➡️ NEXT ACTION that nothing in the owner's hands blocks. When the first item is blocked (a merge,
an approval, a triage, a ruling), name the blocker and whose hand it's in, and take the next
unblocked item in the roadmap's order; a session never idles on the owner while the roadmap has
unblocked work. Ask only when two lanes are equally next and the roadmap doesn't order them.

Write the brief to `~/.claude/projects/<project-key>/sessions/<yyyy-mm-dd-HHmm>-<slug>.md`
(next to `handoffs/`: outside the repo, so it is never committed, and inside Claude Code's own
project data, so it survives the scratchpad; create the folder if it's missing). Continuing an
open brief: append to it instead of writing a new one; when the lane changes, move the old brief
to `closed/` with a one-line pointer to the new one, so only one brief is ever open. Its shape:

```
# Session brief — <yyyy-mm-dd> — <slug>
**Goal:** <one line> · **Lane:** BUILD <spec or issue, slice k> | RESEARCH | DESIGN | HARNESS | TRIAGE | SITTING <spec> · **Roadmap item:** <the tick it advances>

## Why now
<the 📍, and what this session unblocks>

## Scope
**In:** … · **Out:** … (named, so a discovery is slotted, not absorbed)

## Research to carry
<the repo's research docs that bear on this lane, cited by section id; "none" when the repo keeps none>

## Open items
| Item | Home (#issue / spec question / PR) | Blocks this session? | Whose hand |
|---|---|---|---|

## Plan
<the steps in order, one agent or skill per step: the expert agent from the CLAUDE.md roster when the repo has one, else the lead itself; the skill (/interview-me, /spec, /verify, /ship) per step>

## Done when
- [ ] <observable: a check's result, a PR state, a file, a verdict> — proof: <how /wrap-session checks it>

## Owner's decisions needed
- <decision> — REC: <recommendation and why>
```

Rules for the brief: every open item already has a home or gets one now (an issue, a spec
question, a PR). "Blocks" is yes only when a Done-when item can't be met without it. Each
Done-when line is something a cold reader can check. The plan names one agent per step, never
two at once.

## 5 — Kick off

In this same turn, hand the brief to `/orchestrator` with its path: `/orchestrator <brief path>`
.
Single-step work goes through it too (it reads the brief, runs the one step, and closes through
`/wrap-session`). The one exception is a session with nothing unblocked: report that with the
blockers and whose hands they're in, and stop. End every working session with `/wrap-session`.
