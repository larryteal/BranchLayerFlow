# Google Calendar — List + Create Event

Two-agent flow: `ListAgent` enumerates the user's calendars; `CreateAgent` adds an event one day from now to the first (or `target_calendar`).

## Setup

1. In Google Cloud Console enable the Calendar API.
2. Create an OAuth client of type *Desktop app*, download `credentials.json`, and place it at `examples/google-calendar/credentials.json`.
3. First run will open a browser to authorize; the result is cached in `token.json`.

## Run

```bash
uv run --project examples/google-calendar python examples/google-calendar/main.py
```
