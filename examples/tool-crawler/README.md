# Tool — Domain-Bounded Crawler

Crawls up to N pages within one domain, then fans out an LLM analyser per page in parallel. Summary + topic tags collected back into the store.

## Demonstrates

- Crawler returns synchronously; agent uses `loop.run_in_executor` to keep the pipeline async-friendly
- Dynamic team summoning: the crawler's `handoff` builds a fan-out `AsyncParallelBaseFlow` whose branch count depends on the crawl result
- Per-page analyser is the unit of concurrency

## Run

```bash
export OPENAI_API_KEY=sk-...
export CRAWL_SEED=https://example.com/   # any same-domain root
uv run --project examples/tool-crawler python examples/tool-crawler/main.py
```
