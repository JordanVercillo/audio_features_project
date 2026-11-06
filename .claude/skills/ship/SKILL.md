---
name: ship
description: Turn finished, verified work into a reviewed pull request, sized to the change. A slice, a feature, a large diff or several defects gets its own PR (branch check, verify, code-reviewer gate, PR from the template, auto-fix on, CI); a small change or single defect is committed and pushed to the open batch PR instead, where the repo keeps one. TRIGGER when the user says "/ship", "open a PR", "ship it", when /orchestrator reaches its gate phase, or whenever a small fix is ready to commit. SKIP if verify is red (fix first).
user-invocable: true
allowed-tools: [Bash, PowerShell, Read, Grep, Glob, Agent, Skill, mcp__ccd_pr__get_status, mcp__ccd_pr__set_monitor, mcp__ccd_pr__bind_pr]
---

The repo's conventions come first: read `CLAUDE.md` (branch names, labels, whether PRs open as
drafts, whether a batch PR exists, which generated files travel with a change) and
`notes/PROJECT_CONTEXT.md` before step 0. Where this skill and the repo disagree, the repo wins.

0. **Does this need its own PR?** Only a slice, a feature, a large diff or several defects does.
   A small change or single defect goes to the open batch PR instead, where the repo keeps one:
   `/verify` green, commit on its `batch/<yyyy-mm-dd>` branch, push, add its row (and any
   `Closes #n`) to the PR body, then re-check auto-fix (step 6). No batch PR open and the repo
   uses them? Create the branch from `main` and open it as a draft ("Batch <date>: …", an items
   table in place of the slice line); step 3 reviews the whole batch at hand-over, and a commit
   after that verdict gets a delta review before the owner merges. A repo without batch PRs
   commits a small fix on a short-lived branch and opens a small PR.
1. **Branch:** never ship from `main`. Use the repo's branch scheme; the default is
   `<type>/<name>` with `type` one of `slice`, `spec`, `fix`, `chore`, `research`, `batch`. A
   branch behind `main` is synced the way the repo says (the app's `sync_with_base_branch` in a
   worktree, else `git merge origin/main`); a conflict is reported, never resolved silently.
2. **Verify:** regenerate anything the repo generates from the files the slice touched (views,
   an index, a manifest), so the committed copies match a fresh run. Then run `/verify`. Every check green, or "not applicable"
   with its reason. Keep the verdict table.
3. **Review gate:** when the repo has a `code-reviewer` seat in `.claude/agents/`, spawn it (one
   agent, alone) with the spec and slice (for a batch: its items table and the decision or
   issue behind each item), the diff (`git diff main...HEAD`), and the verify verdict.
   APPROVE → continue. Findings → fix them, re-verify, re-review. **A review that terminated
   early is a HOLD.** A MINOR never holds a PR: fix it in the same round when it's cheap,
   otherwise it rides the batch PR or an issue. A repo without the seat says so in the PR body
   ("no reviewer seat; owner reviews") and continues.
4. **Commit hygiene:** small, reviewable commits with messages ending in the attribution trailer
   the system prompt gives. Regenerated files travel with the change that caused them. Nothing
   generated, scratch or evidence-only is committed.
5. **Open the PR.** First carry the spec's bookkeeping, where the repo keeps it (a ✅ on the
   slice's line, the guide's WHERE). Fill in `.github/pull_request_template.md` when the repo
   has one (spec + slice, what changed, acceptance evidence, the verify verdict, the reviewer
   verdict, screenshots or a demo note for a visible change, attached, never committed); without
   a template, those same headings. Link the issue (`Closes #n`). Add the repo's labels.
   `gh pr create --base main --title "<what the change is>" --body-file <filled body>`, with
   `--draft` when the repo's convention opens PRs as drafts (marked ready by the wrap commit).
6. **Auto-fix stays on** (the app defaults it off and doesn't carry it between PRs or sessions).
   Right after creating the PR, and after every later push to it: `mcp__ccd_pr__get_status`. If
   `monitor.auto_fix` is false, call `mcp__ccd_pr__set_monitor` with `auto_fix: true`,
   `address_comments: true` and the PR's url. If the PR isn't bound to this session, bind it
   first (`mcp__ccd_pr__bind_pr`).
7. **CI:** auto-fix watches it and wakes the session on a failure; read the state with
   `mcp__ccd_pr__get_status` rather than polling `gh`. No `mcp__ccd_pr__*` tools in this session
   (a plain terminal)? Use `gh pr checks --watch`, and say auto-fix couldn't be checked.
8. **Hand to the owner:** the PR link, the gates passed, anything that needs the owner's eyes or
   hands (a reload, an import, a page to open). **The owner merges.** Never merge and never
   enable auto-merge.
