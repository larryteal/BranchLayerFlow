# Communication — Three Agents Talking Through `store`

Three agents take turns: one collects input, one accumulates totals, one prints the rolling stats. They never call each other directly — every exchange happens through the shared `store`.

## Demonstrates

- `store` as the only communication channel between agents
- Stable cross-iteration state (`store["totals"]` survives every round)
- A loop expressed by three agents whose `handoff` keeps returning the next one
- Termination is a `handoff` that returns `()`

## Run

```bash
uv run --project examples/communication python examples/communication/main.py
```

Type any text, press `q` to exit.
