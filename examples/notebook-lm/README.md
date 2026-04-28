# NotebookLM-Style Podcast — Doc → Two-Voice MP3

Four-agent pipeline: extract nuggets → generate dialogue script → per-line TTS → merge into one MP3. Two hosts (Alex with `alloy`, Jamie with `echo`).

## Demonstrates

- Heterogeneous tool integration (chat completion + TTS API + audio mixing)
- Per-line work serialised inside one agent; trivially convertible to parallel
- Output paths flow through `store` — no global state

## Run

```bash
export OPENAI_API_KEY=sk-...
# `pydub` needs ffmpeg installed (`brew install ffmpeg`)
uv run --project examples/notebook-lm python examples/notebook-lm/main.py
```
