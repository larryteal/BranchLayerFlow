# Gradio HITL — Travel Assistant With LLM Routing

Gradio `ChatInterface` in front of a routing flow: a `RouteAgent` classifies each user message, then dispatches to one of three handlers (weather, booking, follow-up). All three handlers are siblings under the same router; the dispatch decision is data-driven.

## Demonstrates

- LLM-driven dispatch from a single agent (`RouteAgent.handoff`)
- Multiple typed handlers as peer successors of one router
- The Gradio layer is a thin call site; the same flow runs from CLI just as well

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/gradio-hitl python examples/gradio-hitl/app.py
```
