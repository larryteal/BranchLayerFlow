# Lead Generation — Scrape → Enrich → Score → Personalise

A four-stage linear pipeline mirroring a real sales workflow. Each stage adds one column to the lead records; the final stage drafts cold emails only for leads scoring 6+.

## Demonstrates

- Sequential pipeline with each agent enriching the same shared dataset
- Filter-on-write (`PersonaliseAgent` skips low-score leads) — no special filter primitive

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/lead-generation python examples/lead-generation/main.py
```
