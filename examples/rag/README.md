# RAG — Two-Phase Index + Query

Two separate Flows that share the same `store`: an offline index flow (chunk → embed → FAISS) followed by an online query flow (embed query → retrieve → generate).

## Demonstrates

- Multiple Flows operating on the same `store`
- A long-lived FAISS index passed across runs simply by leaving it in `store`
- Flow factories return fresh agent graphs — but Python objects in `store` persist as long as the caller keeps the dict alive

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/rag python examples/rag/main.py
```
