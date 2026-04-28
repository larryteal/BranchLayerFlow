# Tool — OpenAI Embeddings

Wraps the OpenAI embeddings API as a tool. Two-agent pipeline: embed → similarity report. Loads `OPENAI_API_KEY` from env or `.env`.

## Demonstrates

- Clean tool/agent separation (`tool_embed.py` for the API call, `flow.py` for orchestration)
- A single-shot pipeline that doubles as a sanity test for an external API integration

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/tool-embeddings python examples/tool-embeddings/main.py
```
