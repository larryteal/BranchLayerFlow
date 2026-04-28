# LLM Streaming — Tokens to Stdout, ENTER to Interrupt

Single agent streams chunks to stdout. A daemon stdin-listener thread sets an `Event`; the streaming loop checks it on each chunk and exits gracefully. Whatever accumulated before interrupt is what `store["response"]` ends up holding.

## Demonstrates

- Long-running cooperative work inside `takeover`
- Cancellation via a `threading.Event` flag — pure Python, no special framework feature
- Default uses a fake stream so the demo runs offline; `USE_REAL_LLM=1` switches to OpenAI streaming

## Run

```bash
uv run --project examples/llm-streaming python examples/llm-streaming/main.py
# real LLM:
USE_REAL_LLM=1 OPENAI_API_KEY=sk-... uv run --project examples/llm-streaming python examples/llm-streaming/main.py
```
