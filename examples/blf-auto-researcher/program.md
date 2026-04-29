# Autoresearch program (human-edited control file)

This file is the **only thing** the human edits during a run. Everything
else -- the loop in `flow.py`, the locked evaluator in `judge.py` -- is
contract. The loop reads this file, applies the constraints, then climbs.

## Goal

Produce the highest-scoring research report on the topic supplied via
the command line, where "score" is whatever `judge.py` returns.

## Mutation menu (organized by which judge axis they target)

Every round, each proposer picks ONE mutation that targets the axis the
judge surfaced as weakest. Match the mutation to the axis.

**TOPIC_FIDELITY (25 pts)** -- the most common bottleneck. Trim drift.
   - REMOVE a section that doesn't directly answer the literal question
   - REWRITE a tangential section to refocus on the asked-about thing
   - REPLACE generic comparisons with question-specific ones

**FACT_GROUNDING (25 pts)** -- the second most common bottleneck.
   - REMOVE a specific claim (number, date, name, version, technique)
     that is not supported by WEB FACTS
   - REPLACE an unsupported claim with one you can ground in a WEB FACT
   - HEDGE an under-supported claim ("limited evidence suggests...")
   - DROP an invented URL; only cite verbatim WEB FACTS URLs

**COVERAGE within scope (15 pts)**
   - ADD a missing on-topic sub-aspect the question implies
   - Do NOT add tangential sections to "improve coverage" -- it backfires

**DEPTH (15 pts)**
   - REPLACE a list of facts with a synthesis (mechanism, comparison,
     tradeoff) where WEB FACTS supports it

**STRUCTURE (10 pts)**
   - Add a TL;DR or Caveats section if missing
   - Reorder or split sections for clearer flow

**NOVELTY (10 pts)**
   - Surface a non-obvious angle WITHIN the scope; do not drift to
     novelty by going off-topic

Length is NOT a quality axis. Padding loses points; truth and on-topic
focus gain points.

## Stop conditions

The loop exits when ANY of:

- best score `>= target_score`           (default 90)
- `round >= budget`                       (default 8)
- `streak_no_improvement >= patience`    (default 3)

## Constraints (do not violate)

- Never edit `judge.py` -- if you do, all prior scores become incomparable.
- Never edit `flow.py` from inside the loop.
- Mutations must be expressible as a one-line description in the journal.
- Citations must come from the WEB FACTS supplied at seed time. Do not
  invent URLs.
