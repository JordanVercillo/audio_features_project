---
name: spec
description: Turn a feature idea into a validated, implementable spec through a short interview — the frozen design contract the build reads from and does not overwrite. TRIGGER when the user says "/spec", "write a spec for X", "let's design X before we build it", or before any non-trivial feature. SKIP for a one-line change (just do it), for orientation (use /resume).
user-invocable: true
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Skill]
---

You turn a rough idea into a **validated implementation spec**, the frozen contract the build
reads from. You are a guide, not a co-author: draw the design decisions out of the owner, don't
invent them. Once written, code reads the spec but never overwrites it; if the design changes
mid-build, come back here and re-spec.

## Phase 0 — Recall, and find the repo's contract

Read `notes/PROJECT_CONTEXT.md` (status, conventions, key files) so the spec fits what already
exists: reuse the real modules and schemas, don't design in a vacuum. If the feature touches LLM
work and the repo has a knowledge base (`llm_knowledge_base/` or a `kb-librarian` agent), pull
the matching technique card first.

Then look for the repo's own spec contract, in this order:
- `specs/README.md` or `specs/_TEMPLATE.md` plus a lint the `CLAUDE.md` names (`spec_lint.py`
  or similar): **the repo's format and lint win.** Follow the template's sections, its status
  flow (DRAFT → IN REVIEW → APPROVED → BUILT) and its id scheme; only the owner's word moves a
  spec to APPROVED.
- Otherwise the **YAML contract** below, validated by the script bundled with this skill.

## Phase 1 — Interview (one question at a time; extract the *why*)

Ask, waiting for each answer before the next, with a recommendation attached to every question
(the `/interview-me` laws apply): probe reasoning, don't supply it.
1. **Goal**: what does this do, and why does it matter now?
2. **Approach + decisions**: the key design choices, and for each what was chosen, what was
   rejected, and *why* (this becomes `approach.decisions`).
3. **Tasks**: the concrete steps to build it (module, functions, edge cases), PR-sized and ordered.
4. **Integration**: which existing files or schemas it extends; what stays unchanged; what's read-only.
5. **Evaluation + success**: how it is measured; the minimum bar ("runs, valid output") and the
   good bar ("meets the goal").
6. **Verification**: the exact commands or steps that prove it works end to end; each acceptance
   criterion observable by a cold reader.
7. **Pitfalls**: known traps worth flagging to the implementer (the journal is a source).

Keep it to the decisions that matter; a small feature needs a small interview. Any gap stays an
explicit open question with a recommendation, never filled silently. Numbers nobody ruled are
labelled PROPOSED.

## Phase 2 — Write the spec

Default home: `specs/<feature>_spec.yaml` (create `specs/` if the repo has none). Fill every
section from the interview, in the owner's own reasoning where possible. No code: prose
instructions the implementer adapts. One home per fact: link another spec's decision or a doc's
section, never copy it.

```yaml
approach:
  summary: >   <one paragraph: what gets built and why>
  decisions:
    <key>: { choice: >  <what was chosen>, reasoning: >  <why; what was rejected> }
tasks:
  task_1: { name: <imperative title>, details: |  <step-by-step, concrete> }
integration_steps:            # what to extend / leave unchanged / keep read-only
  - <...>
evaluation_plan: { metrics: [<...>], dataset: <...>, baseline: >  <or "none — new"> }
reference_materials:          # inputs to learn from, not copy
  reused_modules: [<existing code this builds on>]
success_criteria: { minimum: >  <runs + valid>, good: >  <meets the goal> }
verification:                 # runnable acceptance checks
  - <command + what correct output looks like>
known_pitfalls: [ "<trap + the fix>" ]   # optional
```

Required: `approach, tasks, integration_steps, evaluation_plan, reference_materials,
verification`. Recommended: `success_criteria`.

## Phase 3 — Validate (loop until it passes)

Make well-formed a fact, not a judgment. The validator ships with this skill:

```bash
uv run .claude/skills/spec/validate_spec.py specs/<feature>_spec.yaml
```

Parse the JSON (`valid`, `missing_sections`, `warnings`). If not valid, add the missing sections
and re-run until `valid: true`; address warnings too. A repo with its own lint runs that instead,
until it reports ok.

## Phase 4 — Hand off

Report: `Spec saved to <path> · Validation: PASSED · Warnings: …`. Then give the one line that
starts the build, e.g. *"Implement the spec at `specs/<feature>_spec.yaml`"* (directly, or via
`/orchestrator` for a multi-domain build, or the repo's own partner skill named in `CLAUDE.md`).
The implementer **reads** the spec and writes code; it never edits the spec.
