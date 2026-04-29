# blf-react-agent

A tool-using **reason -> act -> observe** loop with two real tools and an
explicit `finish` action:

```
ThinkAgent --(tool == finish or budget spent)--> FinalizeAgent
       |
       v   else
   ActAgent  (web_search | news_search)
       |
       v
   ThinkAgent  (next iteration)
```

Why it shows off BranchLayerFlow:

- The full control flow is **three `>>` lines**:
  ```python
  think >> act >> think     # loop
  think >> finalize         # exit
  ```
  No state machine, no router class, no scheduler — `ThinkAgent.handoff`
  just returns one of its wired successors by name.
- `ActAgent` is the only place tools live; adding a new tool means adding
  a branch in its `takeover`, not editing the flow shape.

## Run

```bash
export OPENAI_API_KEY=sk-...
# optional
# export OPENAI_BASE_URL=https://api.deepseek.com
# export OPENAI_MODEL=deepseek-chat

uv run python main.py "What is the most recent published score of an open-weight model on SWE-bench Verified?"
```
