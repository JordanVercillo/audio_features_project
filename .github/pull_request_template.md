## What this does

<!-- One paragraph in the user's terms, not code terms. For harness or tooling PRs: what it changes
     about how we work. -->

## What changed

<!-- One or two sentences, in code terms. -->

**Spec / slice:** <spec> slice <k>: <name> · Closes #<issue>

## Acceptance evidence

<!-- Each acceptance criterion → the test, command output or demo step that proves it. -->

| Criterion | Proven by |
|---|---|
| | |

## Merge risk

<!-- Door type: two-way (one revert undoes it) or one-way (a migration, a schema change, a
     vendor import, a value baked into data). Blast radius in a word or two: a file / a module /
     the pipeline / the harness. -->

**Door:** two-way · **Blast radius:**

## Gates

- [ ] `/verify` green (paste the verdict line)
- [ ] `code-reviewer` verdict: **APPROVE** (paste the summary; an incomplete review is a HOLD)
- [ ] `uv run scripts/harness_guards.py` green
- [ ] Generated files rebuilt, none hand-edited
- [ ] Visible change? Screenshot or demo note attached

## Notes for the owner

<!-- Anything that needs a human's eyes or a ruling. -->
