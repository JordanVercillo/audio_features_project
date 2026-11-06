---
name: interview-me
description: The relentless interview — pin down a rule, system, spec or plan until nothing load-bearing is ambiguous, ONE question at a time, each with a recommendation. TRIGGER when the user says "/interview-me", "grill me", "interview me", "poke holes", "let's rule <spec>", "let's be specific", or when any seat is about to APPROVE a spec and finds load-bearing ambiguity. SKIP when the ambiguity is a FACT a tool can look up (read the code, the spec, the docs, the repo's research; never ask the owner what the repo already knows).
user-invocable: true
allowed-tools: [Read, Grep, Glob, Bash, AskUserQuestion, Edit, Write]
---

You are running **the interview**, the method used when a rule, system, spec or plan must be
certain before it is captured. Adapted from Matt Pocock's `grill-me`. The goal isn't to fill a
template. It's that **nothing load-bearing can be read two ways** when the interview ends.

Where rulings are recorded is the repo's call: its `CLAUDE.md` or `specs/README.md` names the
home (a spec's decision log, a rulings file, a decisions doc). If none is named, the spec being
ruled gets a dated decision log, and a ruling with no spec goes to `notes/journal.md` as a dated
entry. Read that before the first question.

## The five laws

1. **ONE question at a time.** Ask, wait, incorporate, then ask the next. Batches get shallow
   answers; sequencing lets each answer reshape the next question.
2. **Facts are researched; only DECISIONS are asked.** Before any question, check whether the
   repo already knows (a spec, a decision log, the docs, the code, a research note, the journal).
   If it does, cite it. Every question carries a premise, so check it first: the owner answers
   the question you asked, and an unchecked premise slips a claim past the one person who rules.
3. **Every question carries a RECOMMENDATION.** Always "here's the choice, my REC and why, what
   the alternative costs", never an open-ended "what do you want?". "Use your REC" is a valid
   answer. When the owner overrules a REC, ask the reason in the same ask (so it costs no second
   round), **capture it verbatim**, and replay it against the rulings already made before the
   next question. A pick over the REC with no reason is re-shown once ("is this the one you
   meant?").
4. **A worked example is CHECKED.** When the owner gives an example, replay it against the rule
   as you understood it (arithmetic and all) and say which general rule you extracted.
5. **The shared-understanding gate.** You're done only when you've played the whole design back
   in your own words, the owner has confirmed it, and every number, format and route has a NAMED
   HOME (a decision row, a data column, a doc section). Anything still fuzzy gets one more
   question or stays an explicit open question with a REC. Never smooth it over silently. The
   playback comes after every reason, never before.

## The flow

1. **Frame:** what is being pinned down and what's waiting on it (which spec, which slice, which
   seat's next run). For a thing with a shape (a vision, a system's parts, an order of events),
   ask the owner's own shape of it first, before any question inside it.
2. **Research sweep:** resolve every fact-shaped ambiguity from the repo first; report what you
   resolved, with citations. "We said previously" is searched (this repo, and the sibling repos
   the owner names) before the replay, and told where it was or that it wasn't.
3. **The decision tree:** list the open decisions in dependency order (answers that reshape later
   questions go first), then walk it: one question, one REC, one answer, capture, next. For a
   spec, the tree is its open-questions section, blocking ones first. Use `AskUserQuestion` with
   the REC as the first option, marked "(Recommended)"; price every clause of every option, not
   only its headline. When a question is about order, play the causal chain back as a numbered
   sequence first.
4. **Playback:** the whole design in your words, with every number and its home. When any
   answer touches a date, play back the whole dated timeline before capturing.
5. **Capture:** each ruling goes to the repo's home for rulings (date, ruling, **why**, with the
   owner's words). The open question leaves its doc: struck through with a pointer to the ruling,
   and the doc's text updated to state the ruling as decided. Acceptance criteria become
   observables a reviewer can verify; the spec's status moves (DRAFT → IN REVIEW → APPROVED when
   no blocking question remains; only the owner's word moves it to APPROVED). Then run the repo's
   spec lint, if it has one. A ruling that lives only in the transcript doesn't exist.

## House rules

- **Numbers need homes in the same breath** they're ruled.
- **Disagree before capture, not after.** If a ruling collides with another ruling, a doc or a
  verified fact, say so in the next question; a collision is checked against the old ruling's
  Why, not its headline.
- **Never invent content to fill a gap.** An unanswered number stays PROPOSED or an open question.
- **A ruling that changes another repo** gets a handoff note for the owner to file there; it
  isn't changed from here.
