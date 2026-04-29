# blf-wide-research

Wide breadth-first research with **dynamic parallel fan-out**:

```
DecomposeAgent
     |
     v
ParallelInvestigateFlow  (N branches in parallel; N decided at runtime)
     |   each branch is its own sub-flow:
     |     SearchAgent -> SummarizeAgent
     v
AggregateAgent  (fired by the parallel flow's closing-rite handoff)
```

Why it shows off BranchLayerFlow:

- The parallel flow's branch count is **chosen by an agent at runtime** —
  `DecomposeAgent.handoff` builds a fresh `AsyncParallelBaseFlow` from the
  sub-questions it just produced.
- Each branch is itself a tiny flow (`Search -> Summarize`). Nested flows
  compose without any extra orchestration code.
- The aggregator is wired as the parallel flow's **closing-rite successor**,
  so it fires automatically once every branch drains — no join logic.

## Run

```bash
export OPENAI_API_KEY=sk-...
# Optional: any OpenAI-compatible endpoint works
# export OPENAI_BASE_URL=https://api.deepseek.com
# export OPENAI_MODEL=deepseek-chat

uv run python main.py "How are agentic browsers changing web automation in 2025?"
```

The web search backend is the public HTTP service at
`https://web-search-cat.lessx.xyz` (override with `WEB_SEARCH_URL`).
