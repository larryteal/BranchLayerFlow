# Autoresearch program (human-edited control file)

This file is the **only thing** the human edits during a run. Everything
else -- the loop in `flow.py`, the locked evaluator in `judge.py` -- is
contract. The loop reads this file, applies the constraints, then climbs.

## Goal

Produce the highest-scoring research report on the topic supplied via
the command line, where "score" is whatever `judge.py` returns.

## Mutation menu

Each round, every proposer picks ONE small, motivated mutation from this
menu (or invents a similarly small one). Smaller diffs are preferred --
a 0.5-point improvement that adds a paragraph beats a 1-point improvement
that bloats the report by a section.

- Add a missing factual section the topic obviously requires
- Cite a specific source from the web facts for an unsupported claim
- Tighten or remove a fluffy paragraph
- Rebalance the report structure (move, merge, or split sections)
- Deepen or correct a specific claim that the judge breakdown flagged
- Remove redundancy across sections
- Fix a structural issue (missing TL;DR, weak intro, no caveats)

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
