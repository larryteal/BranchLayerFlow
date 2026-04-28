# Debate — One-Round Pro / Con / Judge

Three agents in a linear pipeline: FOR builds the case, AGAINST reads it and rebuts, JUDGE reads both and picks a winner with reasoning.

## Demonstrates

- A pipeline where each stage's prompt depends on the prior stage's output (read from `store`)
- Adversarial reasoning structured by composition — no special "debate" primitive needed
- The judge is just another agent at the end; you could swap it for a synthesizer, summarizer, or vote tally

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/debate python examples/debate/main.py
```
