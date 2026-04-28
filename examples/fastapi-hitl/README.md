# FastAPI HITL — Process → Wait → (Approve | Reprocess)

The flow's `WaitAgent` blocks on a per-job `threading.Event`. A `POST /jobs/{id}/review` endpoint sets the event with the user's decision; on approve the loop terminates, on reject it loops back to processing.

## Demonstrates

- Synchronous human approval inside an asynchronous server: the agent simply blocks; the HTTP layer wakes it
- One flow body works for any UI (CLI, FastAPI, Slack bot) by swapping the wait mechanism

## Run

```bash
uv run --project examples/fastapi-hitl python examples/fastapi-hitl/server.py
# Terminal 2:
JID=$(curl -s -X POST http://127.0.0.1:7822/jobs -H 'Content-Type: application/json' \
  -d '{"text": "Hello, BLF!"}' | python -c "import json,sys; print(json.load(sys.stdin)['job_id'])")
curl -N http://127.0.0.1:7822/jobs/$JID/events &
# After "awaiting_review" event appears, send a decision:
curl -X POST http://127.0.0.1:7822/jobs/$JID/review -H 'Content-Type: application/json' -d '{"decision": "reject"}'
curl -X POST http://127.0.0.1:7822/jobs/$JID/review -H 'Content-Type: application/json' -d '{"decision": "approve"}'
```
