# Newsletter — Curate → Filter → Summarise → Format

Four-stage linear pipeline: search the web for several topics, filter the most newsworthy, write blurbs, format markdown.

## Demonstrates

- Each stage's output is the next stage's input via the shared `store`
- Source attribution preserved through the pipeline (`href`)
- Set `OFFLINE=1` to skip live DuckDuckGo and use canned snippets

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/newsletter python examples/newsletter/main.py
```
