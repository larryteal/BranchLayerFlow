# Structured Output — YAML-Constrained Resume Parsing

Single agent that asks the LLM for YAML output, parses it, and validates required keys are present. Reparse on failure (up to `meta.max_retries`).

## Demonstrates

- Prompt-based structured output (no provider-specific JSON-mode required)
- Retry as a `for` loop inside `takeover` — when retry semantics are tightly coupled to validation, it can live with the work itself instead of in a separate `_takeover` wrapper
- The store carries the raw text in, the parsed dict out

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/structured-output python examples/structured-output/main.py
```
