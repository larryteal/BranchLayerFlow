# Invoice — Vision Extraction + Arithmetic Validation

Three-stage pipeline: PDF → page images → YAML extraction (vision) → arithmetic checks (line totals, subtotal, tax, grand total).

## Demonstrates

- Heterogeneous pipeline mixing tool calls (PDF, vision API) and pure-Python validation
- Validation errors accumulate in `store["validation_errors"]` for downstream consumption

## Run

```bash
brew install poppler              # or apt-get install poppler-utils
export OPENAI_API_KEY=sk-...
uv run --project examples/invoice python examples/invoice/main.py path/to/invoice.pdf
```
