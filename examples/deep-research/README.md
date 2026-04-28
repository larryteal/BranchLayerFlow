# Deep Research — Recursive Plan / Parallel-Search / Synthesise

Each round: planner emits 3 queries → 3 search agents run in parallel → extractor consolidates facts → synthesiser decides "sufficient" or "loop with these gaps". Bounded by `max_rounds`.

## Demonstrates

- Recursive map-reduce: each round is a fresh fan-out + reducer
- Dynamic team summoning — the planner's `handoff` returns a freshly-built parallel research sub-flow plus the synthesiser as a peer
- Mixed-peer handoff: `(ResearchFlow, SynthesiseAgent)` schedules them as siblings in the same layer

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/deep-research python examples/deep-research/main.py
```

Search is mocked unless `USE_REAL_SEARCH=1` and `SERPAPI_API_KEY` are set.
