# Streamlit FSM — Image Generation HITL

Three-state flow (`input → generating → review → final`) where Streamlit owns the rendering and BLF owns the state transitions. Each Streamlit re-run drains the BLF flow once; the flow blocks at the review state until the user clicks Approve / Regenerate.

## Demonstrates

- Externally-driven BLF execution: the UI calls `step(store)` once per user interaction
- The store is the FSM state; agents merely advance it
- Same pattern transposes 1:1 to other UIs (Gradio, FastAPI HTML, Slack)

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/streamlit-fsm streamlit run examples/streamlit-fsm/app.py
```
