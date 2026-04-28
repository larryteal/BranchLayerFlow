# Self-Healing Mermaid — Generate → Compile → Fix Loop

Generate a Mermaid diagram from a description, compile it via `mmdc` (Mermaid CLI), and on compile failure feed the error back to the generator. Bounded by `meta.max_attempts`.

If `mmdc` is not on `PATH`, falls back to a header-heuristic check so the example still runs. Install the CLI with `npm install -g @mermaid-js/mermaid-cli` for real validation.

## Demonstrates

- Generator/validator loop with feedback (the validator's error becomes the next prompt's context)
- Retry budget on the validator's `meta`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/self-healing-mermaid python examples/self-healing-mermaid/main.py
```
