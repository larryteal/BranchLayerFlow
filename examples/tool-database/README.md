# Tool — SQLite Database

Demonstrates wrapping a SQLite-backed task manager as a tool used by three agents (seed → complete → report). Connections are context-managed; queries are parameterised to prevent injection.

## Demonstrates

- Tools are plain Python helpers (`tool_db.py`); BLF agents call them in `takeover`
- Per-agent narrow responsibility — each owns one DB action
- No global state; the path to the DB lives in `store`

## Run

```bash
uv run --project examples/tool-database python examples/tool-database/main.py
```
