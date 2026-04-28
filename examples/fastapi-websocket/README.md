# FastAPI WebSocket — Streaming Chat

WebSocket endpoint at `/chat`. Each message runs through an async BLF flow whose `StreamReplyAgent` writes chunks to the WebSocket via a `ws_send` callback in the store. Conversation history persists per connection.

## Demonstrates

- Same flow shape as `chat`, but the agent talks to a callable in the store instead of `print`
- The transport (WebSocket vs stdout vs SSE) is invisible to the agent

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/fastapi-websocket python examples/fastapi-websocket/server.py
# Terminal 2:
uv run --project examples/fastapi-websocket python examples/fastapi-websocket/client.py
```
