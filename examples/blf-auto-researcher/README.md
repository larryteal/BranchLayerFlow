# blf-auto-researcher

An **autonomous hill-climber** that mutates a research report round after
round, keeping mutations that raise the score and reverting the rest, until
the score plateaus or the budget runs out. Each round runs `beam` proposers
in parallel; the highest scorer wins the round.

## The loop

```
SeedAgent
   |  4 parallel angle-searches -> deduped web_facts (the locked reference set)
   |  initial draft from facts -> first scored report on the journal
   v
ParallelBeamFlow         beam = K parallel slot sub-flows
   |   each slot:        ProposeAgent -> ScoreAgent
   v
SelectAgent              pick best candidate; keep iff > best_score; journal
   |
   +-- continue --> ParallelBeamFlow (next round) -- loops back to SelectAgent
   |
   v   else (target / budget / patience hit)
ReportAgent              dumps output/report.md + output/journal.tsv
```

## The seven invariants

| Piece | Where it lives |
|---|---|
| **Locked evaluator** | `judge.py` -- per-axis rubric, fixed prompt, `temperature=0`. Never edit during a run. |
| **Single mutable artifact** | `store["report"]` (dumped to `output/report.md`). Each candidate is a full proposed replacement. |
| **Per-trial budget** | 1 LLM proposal + 1 judge call per slot per round. Total bound = `budget x beam x 2`. |
| **Keep/revert primitive** | `SelectAgent`. `keep` iff `candidate_score > best_score`, else discard. |
| **Append-only journal** | `store["journal"]` -> `output/journal.tsv` with `round, slot, decision, candidate_score, current_best_before, mutation, breakdown`. |
| **Human-edited control file** | `program.md`. Topic, mutation menu, stop conditions, hard constraints. The loop body itself is contract. |
| **Non-stopping loop** | `SelectAgent.handoff` returns either a fresh beam (continue) or `ReportAgent` (stop). No interactive checkpoints. |

## The judge: anti-hallucination + on-topic, language-agnostic

The judge does NOT use word count or fact count as a quality proxy --
those rubrics incentivize fabrication and topic drift. Instead it scores
six independent axes, each with explicit criteria, and returns the
weakest axis plus a suggested next mutation. The two largest axes
(50 of 100 points combined) are **TOPIC_FIDELITY** and **FACT_GROUNDING**.

| Axis | Max | What it measures |
|---|---|---|
| **TOPIC_FIDELITY** | 25 | Does the report answer the LITERAL question? Off-topic sections actively *deduct* points (~3 per drifting section). |
| **FACT_GROUNDING** | 25 | Each substantive claim must be supportable by a WEB FACT snippet. Unsupported claims `-2` each, contradicted `-5` each, invented URLs `-5` each (and floor at 0). This is the anti-hallucination axis. |
| **Coverage**       | 15 | Within the on-topic scope, do all major sub-aspects get addressed? Tangential coverage does not count. |
| **Depth**          | 15 | Real synthesis (comparisons, mechanisms, tradeoffs) vs. listing |
| **Structure**      | 10 | TL;DR + named sections + good balance |
| **Novelty**        | 10 | Non-obvious framings within scope |

Each candidate's per-axis breakdown is printed every round and stored on
the journal -- when the best report plateaus, the per-axis numbers tell
you exactly which dimension is limiting it.

### Note on grounding strength

WEB FACTS are search-result snippets (titles + descriptions), not full
page content. The judge can verify claims that appear in the snippet
text or URL but cannot verify claims that would require reading the
full page. Use a stronger judge model (`JUDGE_MODEL=gpt-4o`) to push
the FACT_GROUNDING ceiling -- a stronger model reads the snippets more
carefully and is harder to fool with plausible-sounding fabrications.

## Why BranchLayerFlow specifically

- The hill-climb loop is **two `>>` lines plus one conditional handoff**:
  ```python
  seed >> select       # name lookup target for SeedAgent.handoff
  select >> report     # name lookup target for stop transitions
  # SelectAgent.handoff returns (build_beam_flow(beam),) to loop, or (report,) to stop
  ```
- Each round runs `beam` proposers **in parallel** via `AsyncParallelBaseFlow`.
  A strict serial reference (1 mutation per round) is `--beam=1`. Higher beam
  is structurally beyond what a single-thread ratchet can do.
- A round body is a tiny per-slot sub-flow (`Propose -> Score`) composed
  inside the parallel container. Three layers of nesting; zero glue code.
- The keep/revert + journal + loop control all live in **one agent**
  (`SelectAgent`). The framework provides the loop, the agent provides the
  ratchet logic.

## Run

```bash
export OPENAI_API_KEY=sk-...
# optional, any OpenAI-compatible endpoint
# export OPENAI_BASE_URL=https://api.deepseek.com
# export OPENAI_MODEL=deepseek-chat

uv run python main.py "What are the production limits of agentic browsers in 2026?"

# Smaller / faster knobs:
uv run python main.py "..." --budget 4 --beam 2 --target 80 --patience 2
```

Outputs land in `./output/`:

- `report.md`   -- the highest-scoring report seen across the whole run
- `journal.tsv` -- per-round trace; one row per `SelectAgent` decision

## Tuning the loop without touching code

Everything that controls *how the loop runs* is exposed:

- `--budget N`     max rounds (or `$BUDGET`)
- `--beam K`       parallel proposers per round (or `$BEAM`)
- `--target S`     stop when best score >= S (or `$TARGET_SCORE`)
- `--patience P`   stop after P no-improvement rounds (or `$PATIENCE`)
- `--out DIR`      output directory (or `$OUT_DIR`)

Everything that controls *what the loop optimizes for* lives in
`program.md` (mutation menu, constraints) and `judge.py` (the rubric).

### Asymmetric judge (recommended)

Use a stronger model for the judge than for the proposers -- a strict TA
grading a student is the dynamic that produces deeper reports:

```bash
export OPENAI_MODEL=gpt-4o-mini    # fast/cheap proposer
export JUDGE_MODEL=gpt-4o          # stricter, more discerning judge
```

With a same-model setup the judge tends to plateau early (the proposer's
output is exactly what the judge would write itself).
