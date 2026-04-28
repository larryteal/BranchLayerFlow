# Map-Reduce — Resume Screening

Map: one `EvaluateAgent` per resume, all running concurrently inside `AsyncParallelBaseFlow`. Reduce: the Flow's closing `handoff` aggregates the per-resume verdicts into summary stats.

## Demonstrates

- Map = same-layer fan-out (one agent per item)
- Reduce = the Flow's closing rite
- `meta.resume_path` per agent — each gets a frozen "business card" pointing to its file

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/map-reduce python examples/map-reduce/main.py
```

First run seeds 5 sample resumes under `resumes/`.
