# Workflow — Three-Stage Writing Pipeline

`outline -> draft -> style`. Each stage is one agent; each one reads what the previous wrote into `store` and adds its own output.

## Demonstrates

- Linear multi-stage pipeline — the most common LLM workflow shape
- Stage handoff via `handoff` returning the next stage's name from `successors`
- The shared `store` accumulates intermediate artifacts (outline, draft, styled article)

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/workflow python examples/workflow/main.py
```
