# Batch Flow — N Sub-Flows, One Per (Image, Filter) Pair

Demonstrates the "Flow IS Agent" composition rule. A `DispatcherAgent` builds one sub-flow (Load → Apply → Save) per (image, filter) pair and returns them all from `handoff` as next-layer peers. Each sub-flow runs against its own private store.

## Demonstrates

- Sub-flows as first-class peers — `handoff` returns a tuple of `BaseFlow` instances
- Dynamic team summoning at runtime (the dispatcher constructs flows in `handoff`)
- Per-pair isolation via per-flow private stores; the outer store only holds the index
- The same `Load -> Apply -> Save` flow factory is reused across every pair

## Run

```bash
uv run --project examples/batch-flow python examples/batch-flow/main.py
```

3 sample images × 3 filters → 9 PNGs in `out/`. First run generates random sample images.
