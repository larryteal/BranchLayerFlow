# Text2SQL — NL → SQL → Execute → Self-Debug Loop

Three-agent pipeline with a debug back-edge: introspect schema → generate SQL → execute. On `sqlite3.Error`, the executor hands off back to the generator with the failure context attached to the store.

## Demonstrates

- Self-correcting tool-use loop bounded by `max_attempts`
- Schema introspection lives in its own agent so it can be cached / replaced independently
- The generator handles both first-shot and retry by checking `store["last_error"]`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/text2sql python examples/text2sql/main.py
```
