# Thinking — Chain-of-Thought Self-Loop

A single agent loops on a hard problem, emitting one reasoning step per turn until it writes `FINAL: ...` (or hits `meta.max_steps`). The loop is a `handoff` that returns `(self,)` while the answer isn't ready.

## Demonstrates

- Self-looping agent with an external termination condition (`store["done"]`)
- A budget cap via `meta.max_steps` — frame opacity makes per-agent budgeting trivial
- Externalized reasoning: the model never has to keep all prior steps in its head — they're in `store["steps"]`

## Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run --project examples/thinking python examples/thinking/main.py
```
