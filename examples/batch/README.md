# Batch — Sequential Per-Item Processing

Translates a markdown document into 8 languages, one at a time, inside a single agent. Demonstrates "one node, internal loop" — in BLF this is just a `for` loop in `takeover`; no batch primitive is needed.

## Demonstrates

- A single agent doing N units of work serially in its `takeover`
- BLF intentionally has no `BatchNode` — composition with a `for` is enough
- For the parallel variant, see `examples/parallel-batch`

## Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run --project examples/batch python examples/batch/main.py
```
