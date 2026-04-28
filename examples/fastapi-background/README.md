# FastAPI Background — Background Job + SSE Progress

`POST /generate` kicks off a writing flow as a background task and returns a `job_id`. `GET /events/{job_id}` streams stage progress via Server-Sent Events.

The flow agents publish progress through a `sink` callback in the store — so the same flow runs unchanged in CLI or HTTP contexts; only the sink differs.

## Demonstrates

- Decoupling the flow from its transport: same `build_writing_flow()` is reusable from CLI, web, queues
- Progress = a write to a thread-safe queue; SSE drains it
- The flow has no notion of FastAPI or HTTP — that lives entirely in the adapter

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/fastapi-background python examples/fastapi-background/server.py
# in another terminal:
JID=$(curl -s -X POST http://127.0.0.1:7821/generate -H 'Content-Type: application/json' \
  -d '{"topic": "BLF and BSP"}' | python -c "import json,sys; print(json.load(sys.stdin)['job_id'])")
curl -N http://127.0.0.1:7821/events/$JID
```
