# blf-auto-researcher

A multi-stage autonomous researcher with a **verification loop** and **two
layers of parallel fan-out** (phases, then drilldowns):

```
PlanAgent
    |
    v
ParallelPhaseFlow         one InvestigateFlow per phase, all in parallel
    |   per-phase flow:   SearchAgent -> ExtractAgent (tags claims [ok]/[weak])
    v
VerifyAgent               round 1: collect [weak] claims
    |
    v   weak found?
ParallelDrilldownFlow     one DrilldownAgent per weak claim, in parallel
    |                     each agent re-searches and rewrites the claim
    v
VerifyAgent               round 2: bounded by `max_verify_rounds`
    |
    v
ReportAgent               drops or hedges anything still [weak]
```

Why it shows off BranchLayerFlow:

- **Two distinct dynamic parallel fan-outs** in the same run — phases
  (decided by the planner) and drilldowns (decided by the verifier) — both
  built inside `handoff()` returns rather than at flow-construction time.
- The **verification loop** is `flow >> self` inside `VerifyAgent.handoff` —
  the drilldown sub-flow's closing-rite handoff routes back to the same
  agent for re-evaluation. No state machine, no router.
- Phases are themselves **two-agent sub-flows** (`Search -> Extract`)
  composed inside the parallel container.

## Run

```bash
export OPENAI_API_KEY=sk-...
# optional
# export OPENAI_BASE_URL=https://api.deepseek.com
# export OPENAI_MODEL=deepseek-chat

uv run python main.py "What is the state of long-context evaluation benchmarks in 2025?"
```
