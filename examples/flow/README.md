# Flow — Interactive Text Transformer Loop

Two agents pass the baton back and forth in a loop until the user quits. Demonstrates handoff-driven control flow without any explicit "loop" or "branch" primitive — the loop is just the natural result of `handoff` returning the other agent.

## Demonstrates

- `>>` registers each agent in the other's successor dict (mutual recognition)
- `handoff` decides at runtime: return a successor to continue, return `()` to terminate this branch
- A loop is just two agents that keep returning each other from `handoff`

## Run

```bash
uv run --project examples/flow python examples/flow/main.py
```

You'll be prompted for text, then offered four transforms (upper / lower / reverse / strip), then asked whether to continue. Press `q` at any prompt to exit.
