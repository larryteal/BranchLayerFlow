# TAO — Thought / Action / Observation Loop

Three agents in a cycle: think about what to do, do it (call a tool), observe the result. Repeat until the agent commits a final answer or the cycle budget is exhausted.

## Demonstrates

- A multi-agent loop where each agent has a single, focused responsibility
- Termination by either (a) committing a final answer (`store["final"]`) or (b) hitting `meta.max_cycles`
- A simple deterministic "calculator tool" inside `ActionAgent` so the example runs without external services

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/tao python examples/tao/main.py
```
