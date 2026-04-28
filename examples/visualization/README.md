# Visualization — Static Mermaid Render

Walks a `BaseFlow`'s registered `successors` and nested `branches`, emits a Mermaid `flowchart TD` to stdout. Flows are drawn as `[[double-bracket]]` nodes; agents as `(rounded)` nodes; containment is a dashed edge.

## Demonstrates

- BLF stores enough static structure (`successors`, `branches`) for a tool layer to render the declared topology
- The *dynamic* topology (driven by `handoff`) is intentionally invisible to a static visualiser — that's where AI dispatch happens

## Run

```bash
uv run --project examples/visualization python examples/visualization/main.py
```

Paste the output into any Mermaid-aware viewer (GitHub markdown, Mermaid Live, etc.).
