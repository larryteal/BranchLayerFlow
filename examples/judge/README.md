# Judge — Evaluator-Optimizer Loop

Generator writes a draft; judge scores it; below-threshold scores loop back to the generator with feedback. Terminates on threshold or `max_attempts`.

## Demonstrates

- LLM-as-judge — the simplest case of "synthesize-then-route" inside `JudgeAgent.handoff`
- Mutual agent registration: `gen >> judge` and `judge >> gen`
- A budget cap (`max_attempts`) lives on the judge's `meta` — frame opacity makes per-agent config trivial

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/judge python examples/judge/main.py
```
