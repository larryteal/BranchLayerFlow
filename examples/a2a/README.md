# A2A — Wrap a BLF Flow Behind an A2A-Style HTTP Endpoint

`server.py` exposes a JSON-RPC endpoint with two methods (`agent.card`, `tasks/send`) shaped after the A2A protocol. `tasks/send` translates the request into a call into an internal BLF flow and returns the answer as an artifact.

## Demonstrates

- BLF needs no special "expose me" machinery — the flow is a function; the adapter is just FastAPI
- Other A2A clients can call this server without knowing it's BLF inside
- The same pattern works for any other interop protocol (gRPC, GraphQL, MCP server)

## Run

```bash
export OPENAI_API_KEY=sk-...
# Terminal 1: start the server
uv run --project examples/a2a python examples/a2a/server.py

# Terminal 2: call it
uv run --project examples/a2a python examples/a2a/client.py "What is BLF?"
```
