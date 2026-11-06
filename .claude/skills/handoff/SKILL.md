---
name: handoff
description: Stop mid-task and write a continuation document for a fresh session, outside the repo, pointing at artifacts instead of repeating them. TRIGGER when the user says "/handoff", "hand this off", "continue in a fresh session", or when context or a usage limit is nearly spent mid-task. SKIP at a clean stopping point (that is /wrap-session).
disable-model-invocation: true
allowed-tools: [Read, Grep, Glob, Bash, Write]
---

A handoff is for the next session, not for the repo. `/wrap-session` saves what is durable
(status, the next action, lessons) and commits it; a handoff carries the live state of an
unfinished task: what was tried, what is half-done, what not to redo. Being user-invoked, it
never starts on its own. Adapted from Matt Pocock's `handoff`.

## 1 — Where it lives

`~/.claude/projects/<project-key>/handoffs/<yyyy-mm-dd-HHmm>-<slug>.md`, where `<project-key>`
is the repo's absolute path with every character that isn't a letter or digit replaced by `-`
(`C:\Users\x\my_repo` becomes `C--Users-x-my-repo`). In a git worktree, use the main checkout's
path, so the handoff lands where that repo's `/resume` looks. That folder is Claude Code's own
project data, so it survives the session; a session scratchpad does not, and nothing in the repo
is scratch. Create the folder if it is missing. `/resume` and the SessionStart hook read the
newest file there.

## 2 — What it holds, in this order, a few lines each

1. **Goal** of the task in one line, and the spec, plan, brief or issue it serves.
2. **Where it stands:** done · in progress (the exact file and what is half-written) · not started.
3. **State of the tree:** branch, `git status --short`, unpushed commits, the open PR and its gates
   (verify verdict date, reviewer verdict, CI). A dirty tree is described, never cleaned. If an
   external tool was mid-change (an editor open on a half-applied edit, an import half done), say so.
4. **Decisions made this session**, each with who made it (the owner, or a seat under a brief)
   and where it is recorded. A decision recorded nowhere yet is flagged, not re-recorded here.
5. **What was tried and failed**, so the next session doesn't repeat it.
6. **Open questions**, each with a recommendation.
7. **Next step:** the first command or edit of the next session, literally.
8. **Suggested skills and seats** for the continuation (`/orchestrator`, `/verify`, a seat named
   in the repo's `CLAUDE.md` roster).
9. **Pointers:** paths, commit hashes, PR and issue numbers, verdict or report files. Never the
   content of a file that exists.

Redact anything secret before writing. If `$ARGUMENTS` names what the next session is for, write
for that use.

## 3 — Close

Report the file path and the Next step line. If the session also did durable work, run
`/wrap-session` after this, not instead of it.
