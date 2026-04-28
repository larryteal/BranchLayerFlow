# Tool — Web Search

Wrap web search as one tool that an `AnalyseAgent` consumes. SerpAPI is the live backend; a canned fallback runs if `SERPAPI_API_KEY` isn't set.

## Demonstrates

- A "tool" in BLF is just a Python function (`tool_search.search_web`) called inside an agent's `takeover`
- Three-stage linear pipeline: input → tool call → LLM analysis

## Run

```bash
export OPENAI_API_KEY=sk-...
# optional: real search
export SERPAPI_API_KEY=...
uv run --project examples/tool-search python examples/tool-search/main.py
```
