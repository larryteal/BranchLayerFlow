# Node — Retry + Fallback by Inheritance

Reusable `RetryableAgent` base that retries `takeover()` up to `meta.max_retries` times and falls back to `fallback(store, error)` if every attempt raises. `SummarizeAgent` subclasses it; users only write the actual work.

## Why this matters

BLF intentionally has no built-in retry/timeout/etc. The framework exposes a seam — the `_takeover` method — where you wrap user-level `takeover` with whatever cross-cutting concern you want. Retry, timeout, tracing, rate limiting are all *your* base classes. The framework stays small; your subclasses are the application.

## Demonstrates

- `_takeover` as the AOP-style override point
- `meta.max_retries` — `BaseMeta` has `extra="allow"`, so any custom field is yours to use
- A `fallback` hook on the agent, invoked when retries exhaust

## Run

```bash
export OPENAI_API_KEY=sk-...
uv run --project examples/node python examples/node/main.py
```
