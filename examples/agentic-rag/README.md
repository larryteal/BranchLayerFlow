# Agentic RAG — Agent Picks Which Doc to Read Next

Instead of a static top-K retrieval, the controller agent inspects document **summaries** and decides one doc to read at a time. After each read, it re-evaluates whether to read more or commit an answer.

## Demonstrates

- LLM-driven dispatch — `handoff` interprets the agent's free-text decision (`READ: doc-id` vs `ANSWER`)
- Stateful loop where each iteration grows `store["read_bodies"]`
- A budget cap on `meta.max_reads` keeps the loop bounded

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/agentic-rag python examples/agentic-rag/main.py
```
