# Parallel Batch Flow — N Sub-Flows Running Concurrently

Same shape as `batch-flow` (one Load → Apply → Save sub-flow per (image, filter) pair) but the outer scheduler is `AsyncParallelBaseFlow` — every sub-flow runs in parallel.

## Demonstrates

- Parallel composition of sub-flows (Flow IS Agent, all sub-flows are peer branches)
- `AsyncParallelBaseFlow` runs same-layer branches concurrently with `asyncio.gather`
- I/O-bound work runs through `loop.run_in_executor` so sync libraries (PIL) don't block
- Per-pair private stores keep each sub-flow's state isolated

## Run

```bash
uv run --project examples/parallel-batch-flow python examples/parallel-batch-flow/main.py
```
