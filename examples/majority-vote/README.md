# Majority Vote — K Voters in Parallel + Tally

Five solver agents tackle the same hard problem concurrently; the tally agent reads `store["answers"]` and emits the most-frequent answer. Demonstrates the canonical scatter-gather shape.

## Demonstrates

- `AsyncParallelBaseFlow` runs all voters at once
- The Flow's closing rite (`handoff`) returns the next layer (the tally), demonstrating "synthesize-then-route" — work happens before the routing decision
- Per-voter `meta.voter_id` keeps each call labelled even though they all share `takeover`

## Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run --project examples/majority-vote python examples/majority-vote/main.py
```
