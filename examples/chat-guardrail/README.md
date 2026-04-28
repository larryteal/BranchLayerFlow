# Chat Guardrail — Topic-Filtered Advisor

Three-agent loop: input → guard → (advisor | back to input). The guard performs cheap heuristics first, then an LLM topic-classifier; only travel queries reach the advisor.

## Demonstrates

- Conditional handoff: `GuardAgent.handoff` picks `advisor` or `input` from `store["verdict"]`
- A guardrail is just an extra agent in front of the worker — no special primitive
- Two-tier validation (cheap rules → expensive LLM call) collapses naturally into one `takeover`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/chat-guardrail python examples/chat-guardrail/main.py
```
