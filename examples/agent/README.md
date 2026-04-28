# Agent — Decide / Search / Answer Loop

A three-agent research loop where the `DecideAgent` looks at the current notes and emits either `SEARCH: <query>` or `ANSWER`. Search agents append snippets to the store; answer terminates the loop.

## Demonstrates

- Conditional handoff that interprets an LLM's free-text decision
- A budget cap (`max_searches`) prevents infinite loops
- Search is mocked by default; set `USE_REAL_SEARCH=1` with `serpapi` to swap in a real backend

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/agent python examples/agent/main.py
```
