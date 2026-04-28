# Batch Node — Split / Process / Combine in One Agent

Streams a CSV in chunks, computes a partial aggregate per chunk, then combines all partials into a final summary. The whole "batch node" is plain Python inside a single `BaseAgent.takeover` — no framework primitive is required.

## Demonstrates

- "BatchNode" reduces to three private methods on one agent
- Memory-bounded streaming for large inputs (we never hold the whole CSV)
- BLF stays out of the way: framework provides the protocol, the algorithm is yours

## Run

```bash
uv run --project examples/batch-node python examples/batch-node/main.py
```

The first run generates a 10 000-row sample `sales.csv`.
