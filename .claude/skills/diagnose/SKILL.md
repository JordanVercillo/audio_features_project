---
name: diagnose
description: "Phase-gated diagnosis for anything red, thrown, failing, flaky, slow, drifting or wrong: a red test, an exception, a build or pipeline stage whose numbers moved, an audit flag, a count that disagrees between two homes, a verify that went red. Use before touching code to fix a defect; the gates stop guesswork."
allowed-tools: [Read, Grep, Glob, Bash, PowerShell, Edit, Write]
---

A fix without a red-capable loop is a guess with a commit message. Work the phases in order; each
gate is met before the next phase starts. Adapted from Matt Pocock's `diagnosing-bugs`; the loop
runs on the repo's own instruments, which its `CLAUDE.md` and `notes/PROJECT_CONTEXT.md` name
(the test command, the guard script, the audit or build script, a lint).

## 0 — Before anything
- Redact: secrets become `<REDACTED>` in anything you quote.
- Read the spec, rule, plan or doc that rules the behaviour. It is the oracle, not the current
  code or output. A behaviour nothing rules is a question for the owner (an open question with a
  recommendation), not a bug.
- Read the repo's known traps first: `notes/journal.md` and any gotchas doc `CLAUDE.md` points
  at. A trap the journal already names is the first hypothesis, not the last.

## 1 — Build the loop (gate: one command, red now)
In rough order of preference: a failing test · the repo's verify, audit or build command with a
filter (its JSON or first error line names the row) · a script that diffs output against a
known-good fixture · a replay with a fixed seed (a moved number at the same seed is the
assertion) · a one-off probe script in the session scratchpad · a profile against a measured
baseline for slowness. Make it fast and deterministic; a flaky bug first gets its reproduction
rate raised. Anything that triggers a reload or a long external process runs async and is polled,
never awaited blind. If no loop can be built, stop and say what you tried and what access,
instrumentation or hand reproduction would unblock it.

## 2 — Minimise (gate: every remaining element is load-bearing)
Smallest input, fewest rows, one seed. Cut one element at a time and re-run after each cut.

## 3 — Hypothesise (gate: 3–5 ranked, falsifiable)
Each one is a prediction: "if X is the cause, changing Y turns the loop green." After the repo's
known traps, check the generic classes: a stale generated file, state leaking between runs,
unseeded randomness or wall-clock reads, unordered iteration, an edit to a file that a tool
regenerates, a path that silently creates an empty resource when missing. An ordering claim is
confirmed only by asserting the order. Show the ranked list before testing it.

## 4 — Instrument (one variable per probe)
Tag every temporary log `[DEBUG-xxxx]` with a unique suffix, in a scratchpad script where
possible, never left in a tracked file. Prefer the test or a probe over log-everything-and-grep.
For slowness, bisect against the baseline before changing code.

## 5 — Fix and regression test (gate: the test failed before the fix)
The regression test lives in the rule's one test home (beside the rule's other tests, an
invariant in the build, a guard), is written failing first, and takes its expected value from
the spec or a worked example, never from the code under test. Then re-run the Phase 1 loop.
Never: suppress the exception, widen a catch or a filter, relax an invariant, re-order without a
test, hand-edit a generated file, or leave a placeholder value.

## 6 — Clean up (gate: the checklist)
- `grep -r "DEBUG-"` over the source folders `CLAUDE.md`'s map names finds nothing.
- Throwaway probes and prototypes are gone from the repo.
- The commit or PR names the hypothesis that proved true, and whether a count, hash or baseline
  moved and why.
- A genuine surprise becomes a `notes/journal.md` entry at `/wrap-session`.
