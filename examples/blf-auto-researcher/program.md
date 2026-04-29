# Autoresearch program (human-edited control file)

This file is the **only thing** the human edits during a run. Everything
else -- the loop in `flow.py`, the locked evaluator in `judge.py` -- is
contract. The loop reads this file, applies the constraints, then climbs.

## Goal

Produce the highest-scoring research report on the topic supplied via
the command line, where "score" is whatever `judge.py` returns.

## Mutation menu (organized by which judge axis they target)

Every round, each proposer picks ONE mutation that targets the axis the
judge surfaced as weakest. Match the mutation to the axis -- a "Specificity"
mutation will not help when the bottleneck is "Novelty".

**Coverage** -- add a missing major sub-topic the question implies
**Specificity** -- replace a generic paragraph with concrete facts (numbers,
   dates, named entities, version strings, URLs from WEB FACTS)
**Sourcing** -- attach a verbatim WEB FACTS URL to a major uncited claim
**Structure** -- TL;DR up top, well-named sections, balance, scannable flow
**Depth** -- swap listing for synthesis: explain mechanisms, compare
   tradeoffs, show why X works where Y doesn't
**Novelty** -- surface a non-obvious angle: a critique, a contrarian
   reading, an under-reported detail, a connection across sources

Length is NOT a quality axis. Padding will not raise the score; the
Specificity axis penalizes thin reports automatically.

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
