# CLI HITL — Joke Generation With Human Approval

Three-agent loop: read topic, generate a joke (using prior rejections as context), ask the user to approve. Reject loops back; approve terminates.

## Demonstrates

- The simplest possible human-in-the-loop pattern: approval lives in `ReviewAgent.handoff`
- Rejected attempts accumulate in `store["rejected"]` so each retry sees prior duds

## Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run --project examples/cli-hitl python examples/cli-hitl/main.py
```
