---
name: verify
description: Prove the project passes every check it defines (the test command, the lint, the harness guards, a build if there is one) and report one table. TRIGGER when the user says "/verify", reports a failing test or build, before committing code, or as the gate inside /orchestrator and /ship. SKIP for pure design conversation.
user-invocable: true
allowed-tools: [Bash, PowerShell, Read, Glob, Grep]
---

Diagnose; don't modify project files. The checks are the ones the repo names: read `CLAUDE.md`
(its ground rules, routing and map) and `notes/PROJECT_CONTEXT.md` (Key files, conventions) for
the test command, the lint, the harness guard script, the spec lint, a build or export, and the
order CI runs them in. A repo whose `.claude/skills/verify/` exists has its own, more specific
list: that skill wins, and this one is only the fallback.

## Run

1. Fast checks first, **all of them, even when an early one fails**: every check reports.
2. Harness guards (where the repo has `scripts/harness_guards.py` or the equivalent its
   `CLAUDE.md` names) run before any generator, with no `--skip`.
3. The test command exactly as the repo runs it (CI's invocation is the reference): the whole
   suite; a subset proves a subset.
4. A build, export or generator check when the repo has one. A generated file that `git status`
   shows changed after the run travels with the change that caused it, or it is a finding.
5. Audits that read **live state** (a warehouse audit, an environment check, an editor bridge)
   run only when the slice touched that state; they are audits, not tests.
6. **The not-applicable exception:** when `git diff <base>...HEAD --stat` touches nothing a check
   reads, that check is "not applicable", reported in those words with the reason; the other
   checks still run. The exception is named per check, never for the whole run.

Save outputs to the session scratchpad, never `/tmp` (Git Bash and Windows Python disagree about
it). Read each tool's own report or JSON, never its build folder.

## Verdict

Report one table: check · command · result · evidence (counts, the verdict line). The verdict is
**PASS** only when every row passes or is not applicable with a reason. A check that died
mid-run, timed out or was skipped is **HOLD**, never a pass; say which and why. **0 tests
executed** (or 0 rows loaded for a table that has rows) is a FAIL, never a skip.

On a failure, quote the first failing assertion or error with its file:line (for a build, the
table, row and invariant it names), then stop: fixing is the caller's job (or `diagnose`'s).
