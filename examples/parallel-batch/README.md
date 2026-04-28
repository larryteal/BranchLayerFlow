# Parallel Batch — Concurrent Same-Layer Fan-Out

Same job as `examples/batch` (translate into 8 languages) but using `AsyncParallelBaseFlow`. All 8 LLM calls happen concurrently via `asyncio.gather`.

## Demonstrates

- Same-layer fan-out: N peer agents in layer 0
- `AsyncParallelBaseFlow` swaps the scheduler from sequential to `asyncio.gather`
- The cross-layer barrier still holds — the run waits until every branch finishes
- Speedup over the sequential `batch` example is roughly the slowest-call ratio

## Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run --project examples/parallel-batch python examples/parallel-batch/main.py
```
