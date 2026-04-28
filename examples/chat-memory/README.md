# Chat Memory — Sliding Window + FAISS Recall

Hybrid memory: a 3-pair sliding short-term window plus a FAISS-indexed long-term archive. Each turn runs four agents:

```
get_user -> retrieve -> answer ---[window full]---> embed --+
                              \--[not full]----------------> get_user
                                                            ^
                                                  embed ----+
```

## Demonstrates

- Multi-agent linear pipeline with a *conditional* fan-in back to the loop start
- A handoff conditional: same `AnswerAgent` routes either to `embed` or back to `get_user` depending on `len(store["recent"])`
- Long-term memory by reference, not by summarization (semantic similarity recall)
- Mutable `store` carries a FAISS index across iterations

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/chat-memory python examples/chat-memory/main.py
```
