# Voice Chat — Mic ↔ Whisper ↔ Chat ↔ TTS Loop

Four-agent loop: record (with simple silence-based VAD) → Whisper → GPT-4o → TTS playback. Conversation history persists in `store["messages"]`.

## Demonstrates

- Heterogeneous I/O agents stitched into one loop
- VAD as plain numpy thresholding inside `ListenAgent` — no extra dependency
- Each agent's responsibility is a single I/O concern; swapping providers means swapping one agent

## Run

```bash
brew install portaudio              # required by sounddevice on macOS
export OPENAI_API_KEY=sk-...
uv run --project examples/voice-chat python examples/voice-chat/main.py
```
