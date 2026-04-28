# Nested Batch — School / Class / Student Hierarchy

Three nesting levels: a `SchoolFlow` whose branches are `ClassFlow`s whose branches are `StudentAgent`s. Each level's `handoff` aggregates what the level beneath it produced. Flow IS Agent, so the only difference between an "outer batch" and an "inner batch" is **which level you're sitting at**.

## Demonstrates

- Recursive composition: Flow inside Flow inside Flow
- The closing rite (`Flow.handoff`) is the natural fan-in / aggregation point
- One `store` carries student averages → class averages → school average
- No "nested batch" primitive — nesting is just composition

## Run

```bash
uv run --project examples/nested-batch python examples/nested-batch/main.py
```

First run seeds 2 classes × 3 students × 5 grade samples per student.
