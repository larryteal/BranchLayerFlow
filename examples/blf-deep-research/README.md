# blf-deep-research

Iterative deepening research with **gap-driven loops** and **parallel search inside the loop**:

```
PlannerAgent       (writes N queries from topic + known gaps)
       |
       v
ParallelSearchFlow (N concurrent web searches; closing-rite -> analyze)
       |
       v
AnalyzeAgent       SUFFICIENT? -> ReportAgent
                    else GAP: lines -> back to PlannerAgent
```

Why it shows off BranchLayerFlow:

- The outer **loop** is just `analyze >> plan` — no scheduler, no state machine,
  the framework re-enters the planner whenever analyze hands off to it.
- Each round **rebuilds** the parallel search sub-flow on the fly, so the
  search width and the queries themselves both come from the planner's output.
- The parallel sub-flow's **closing-rite handoff** funnels the layer back to
  the analyzer once every search resolves — no manual join.

## Run

```bash
export OPENAI_API_KEY=sk-...
# optional
# export OPENAI_BASE_URL=https://api.deepseek.com
# export OPENAI_MODEL=deepseek-chat

uv run python main.py "What are the production limits of agentic browsers in 2025?"
```
