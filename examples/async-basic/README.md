# Async Basic — Recipe Finder With Rejection Loop

Three async agents form a pipeline with a feedback loop:

```
fetch -> suggest -> approve --(reject)--> suggest --(accept)--> done
```

The retry loop is not a special primitive — it's just `ApprovalAgent.handoff` returning `SuggestAgent` again.

## Demonstrates

- `AsyncBaseAgent` with `async def takeover` / `async def handoff`
- `AsyncBaseFlow` that drives the layer schedule with `async for`
- A loop expressed by re-returning a previous successor — no special "edge" type

## Run

```bash
uv run --project examples/async-basic python examples/async-basic/main.py
```

The example uses mocked async I/O (no real API), matching the pedagogical focus on async control flow rather than LLM mechanics.
