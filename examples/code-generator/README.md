# Code Generator — Spec → Tests → Code → Test → Fix

Generate tests, implement, run, decide whether to fix tests or code, retry. The decision lives in `ReviseAgent.takeover` — a small LLM call that classifies the failure.

## Demonstrates

- A four-agent loop with a routing decision in the middle (`ReviseAgent`)
- Tests run via Python's stdlib `unittest`; no external test runner needed
- `meta.max_attempts` budget on `RunTestsAgent`

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/code-generator python examples/code-generator/main.py
```
