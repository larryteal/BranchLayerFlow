# Tracing — Cross-Cutting Observability via Subclasses

`tracer.traced(cls, sink)` returns a subclass of any `BaseAgent` / `BaseFlow` whose `_takeover` and `_handoff` wrap the originals with timing + emission. No decorators on user code — wrap at construction time.

## Demonstrates

- BLF's "cross-cutting concerns are subclasses" philosophy in pure form
- A `Sink` is anything with `emit({...})`; swap for OTel, Langfuse, file, etc.
- The pattern transposes 1:1 to retry, timeout, rate limit, audit logging

## Run

```bash
uv run --project examples/tracing python examples/tracing/main.py
```
