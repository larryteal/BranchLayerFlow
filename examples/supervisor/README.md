# Supervisor — Outer Agent Auditing an Inner Flow

The unreliable workhorse is wrapped in its own `BaseFlow`; the supervisor sits outside and treats that whole flow as just another agent it can re-summon. Bad answers loop the entire research flow back; good answers terminate.

## Demonstrates

- A Flow returned from `handoff` works exactly like a single agent — Flow IS Agent
- Outer-vs-inner separation: the supervisor needs no awareness of how the inner flow does its work
- "Re-run the whole pipeline" is just `handoff -> (research_flow,)`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/supervisor python examples/supervisor/main.py
```

The inner answer is intentionally garbled with 50% probability so the supervisor's loop is observable.
