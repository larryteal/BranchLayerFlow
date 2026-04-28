# Chat — Single-Agent Self-Loop

The simplest conversational pattern in BLF: one agent that keeps returning itself from `handoff` until the user exits. Conversation history lives in `store["messages"]` and persists across loop iterations.

## Demonstrates

- Self-loop via `handoff` returning `(self,)`
- The shared `store` survives layer transitions, so chat history accumulates naturally
- Termination is just a `handoff` that returns `()`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/chat python examples/chat/main.py
```
