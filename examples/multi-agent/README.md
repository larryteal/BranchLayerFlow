# Multi-Agent — Taboo Word Game

Two agents take turns: the Hinter writes a clue while avoiding forbidden words; the Guesser tries to identify the target. They pass the baton until the guess is right (or `max_rounds` is reached).

## Demonstrates

- Inter-agent communication via the shared `store["transcript"]` list — no message queues required, the store *is* the channel
- Alternating handoff: each agent's `handoff` returns the other
- Termination by either side via `handoff` returning `()`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/multi-agent python examples/multi-agent/main.py
```
