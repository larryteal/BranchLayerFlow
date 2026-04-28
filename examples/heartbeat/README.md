# Heartbeat — Outer Wait Loop Wrapping an Inner Flow

`WaitAgent` sleeps and counts cycles; on each tick its `handoff` returns the inner `InboxFlow` plus itself, so the inbox flow runs once and the wait agent then re-fires for the next tick. Termination = `cycle >= max_cycles`.

## Demonstrates

- Mixed-peer handoff: `(inbox_flow, self)` — a Flow and an Agent run as siblings in the same layer
- Self-loop on `WaitAgent` keeps the heartbeat alive
- Inner flow fully reusable; swap it for a Slack watcher, DB poller, etc., without touching `WaitAgent`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/heartbeat python examples/heartbeat/main.py
```
