# Coding Agent — 6 Tools + Patch Sub-Flow

Autonomous LLM-driven coding agent with six tools (`list_files`, `grep_search`, `read_file`, `patch_file`, `run_command`, `done`). The `patch_file` action goes through its own three-step sub-flow (read → validate → apply) so a malformed patch can be rejected before any file is written.

## Demonstrates

- A textbook agent loop (`AgentAgent ↔ ToolAgent`) with a hard step budget
- Patch as sub-flow: the `ToolAgent` injects a sub-flow it owns and drains it inline — sub-flows as building blocks
- The store is the agent's memory; truncation/compression would just be one more agent

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/coding-agent python examples/coding-agent/main.py
```

First run seeds a `sandbox/calc.py` with a missing `mul` implementation; the agent should patch it and run the tests.
