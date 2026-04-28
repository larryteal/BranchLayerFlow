# Hello World — Single-Agent QA

The smallest possible BLF program: one agent reads a question from the shared `store`, calls an LLM, and writes the answer back. Wraps the agent in a `BaseFlow` so you can see the full Flow lifecycle even for a one-step pipeline.

## Demonstrates

- `BaseAgent.takeover(store)` — the unit of work
- `BaseFlow(branches=(agent,))` — the meeting room that schedules the work
- Draining the layer generator with `deque(flow(store=store), maxlen=0)`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/hello-world python examples/hello-world/main.py
```

## Files

- `flow.py` — `AnswerAgent` and the `qa_flow` factory
- `main.py` — entry point
- `utils/call_llm.py` — minimal OpenAI wrapper (reads `OPENAI_API_KEY`)
