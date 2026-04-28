# Agent Skills — Runtime-Selected Markdown Prompts

A "skill" is a markdown file with a system-prompt-style instruction. The selector agent inspects the request, picks one skill from `skills/`, and the apply agent runs the LLM with that file's contents as the system prompt.

## Demonstrates

- Two-stage routing → execution pipeline
- Skill files are *data*; adding a new behavior is dropping a new `.md` into `skills/`
- The selector can be improved freely (rules, embeddings, LLM) without touching the executor

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/agent-skills python examples/agent-skills/main.py
```
