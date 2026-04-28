# MCP — BLF Agent Calling Tools Over Model Context Protocol

A two-agent flow (`plan` → `call`) where both agents open an MCP session against a tiny stdio MCP server (`server.py`) that exposes `add` / `sub` / `mul` tools. The plan agent reads the tool catalogue from the server itself; the call agent invokes the chosen one.

## Demonstrates

- Tools as a remote, discoverable surface (MCP) instead of in-process Python
- Per-agent MCP session — no global client state
- Adding new tools means editing the server, not the agent code

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/mcp python examples/mcp/main.py
```

The agent spawns `server.py` as a stdio subprocess automatically.
