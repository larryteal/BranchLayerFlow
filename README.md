# BLF (Branch Layer Flow)
<p align="center">
  <img src="https://raw.githubusercontent.com/larryteal/BranchLayerFlow/master/logo.png" alt="Branch Layer Flow Logo" width="120" />
</p>
BLF is a lightweight multi-agent orchestration framework that supports parallel execution, loops, and iterative execution.

## Logic Animation
![LogicAnimation](https://raw.githubusercontent.com/larryteal/BranchLayerFlow/master/LogicAnimation.svg)

---

## Why BLF

BLF is a deliberately minimal **kernel** for multi-AI-agent systems. It does not bundle LLM clients, prompt libraries, tool registries, or memory abstractions — those remain yours to choose. What it gives you is the **collaboration protocol** that lets specialized agents take turns on a complex task, hand work off to whoever is best suited next, and synchronize teams when needed.

What this buys you:

- **Stewardship-handover semantics.** Agents work like a relay team. Each agent picks up the in-flight task (`takeover`), contributes its specialty, then passes the baton (`handoff`) to one or many next stewards. The vocabulary is taken from real human work handovers — hospital shift change, military command transfer, relay race — because that is precisely how complex AI tasks naturally decompose.

- **AI-driven dispatch as a first-class pattern.** `handoff` is just a Python method that returns a tuple of next agents — so the routing decision can itself be an LLM call. Each agent owns its own dispatch intelligence (subsidiarity); the topology of any given run **emerges** from local decisions instead of being statically defined upfront.

- **Free composition — Flow IS Agent.** A `Flow` is a subclass of `Agent`, which means it can be returned from any other agent's `handoff` exactly like an individual agent. Mix and nest single agents and entire teams as peers in the same dispatch tuple. There is no "sub-flow" type distinction to design around.

- **BSP-style structural concurrency, with safety by construction.** Layer barriers are built in. Same-layer branches never see each other directly; they communicate through the shared `store` between layers. Switching from sequential to truly parallel execution within a layer is a one-line override (`AsyncParallelBaseFlow` uses `asyncio.gather`), and the cross-layer barrier always holds — so concurrency cannot introduce protocol-level races.

- **Inheritance is the API.** Every framework class is `Base*`. You build your application by subclassing and overriding `takeover` / `handoff`. Cross-cutting concerns (retry, timeout, tracing, concurrency limits, error containment) are also subclasses — there are no plugins, hooks, or middleware to learn. The framework provides the protocol; your subclasses ARE the application.

- **Framework opacity is intentional.** `store: Any` means you bring your own state shape — dict for prototypes, pydantic for production, ORM session or event bus when you need them. `Meta` is `extra="allow"` so you describe your agents however your AI dispatchers need them to be described. The framework never prescribes what an LLM client, tool format, message schema, or persistence layer should look like.

This is the **Unix philosophy applied to multi-agent systems**: a small, transparent kernel that does one thing well (collaboration choreography), composes with anything (opaque store, extensible meta), and refuses to make policy decisions (retry, observability, persistence) that would age out as the LLM ecosystem evolves.

## Installation

```bash
pip install branchlayerflow
```

Requires Python ≥ 3.9. The only runtime dependency is `pydantic`.

## 30-second mental model

Two verbs do all the work:

- **`takeover(store)`** — *"I'm taking over from here; here is my contribution."* Read in-flight state from `store`; contribute your specialty; mutate `store`.
- **`handoff(store)`** — *"I'm done; pass the baton to these stewards next."* Return a tuple of next agents — one, many in parallel, a sub-flow, a mix, or `()` to terminate this branch.

A `Flow` is the meeting room that schedules its branches **layer by layer with synchronization barriers between layers**. The Flow's own `takeover` and `handoff` are the opening rite (once at start) and closing rite (once after the team exhausts) — and the closing rite is where supervision (and often output synthesis) naturally lives.

## Quick example

A linear pipeline `Inc -> Double` running through a Flow:

```python
from collections import deque
from branchlayerflow import BaseMeta, BaseAgent, BaseFlow

class Inc(BaseAgent):
    def takeover(self, store): store["x"] += 1
    def handoff(self, store): return (self.successors["double"],)

class Double(BaseAgent):
    def takeover(self, store): store["x"] *= 2

class Pipeline(BaseFlow):
    pass

inc, dbl = Inc(BaseMeta(name="inc")), Double(BaseMeta(name="double"))
inc >> dbl                                                # register successor
pipeline = Pipeline(BaseMeta(name="pipeline"), branches=(inc,))

store = {"x": 3}
deque(pipeline(store=store), maxlen=0)                    # drain the layer generator
print(store)                                              # {"x": 8} — (3 + 1) * 2
```

For true parallel LLM calls within a layer, swap to the async variants: `AsyncBaseAgent` for agents, `AsyncParallelBaseFlow` for the Flow. Same shape — `asyncio.gather` happens for free inside each layer; the layer barrier still holds between layers.

## Core abstractions — the entire framework surface

| Class | Role |
|---|---|
| `BaseMeta` | Frozen identity card. The framework reads only `name` (used as the successors-dict key). Add any fields you want — they become your agent's "business card" for AI dispatchers to read when picking teammates. |
| `BaseAgent` / `AsyncBaseAgent` | Override `takeover` to do work, `handoff` to dispatch the next stewards. Default implementations are empty — these classes are meant to be inherited. |
| `BaseFlow` / `AsyncBaseFlow` / `AsyncParallelBaseFlow` | A Flow IS an Agent. It opens at `takeover`, schedules its branches layer-by-layer in between, and closes at `handoff` (the team's last word — often a synthesis of the team's output plus a routing decision). |
| `>>` operator | Register a successor in the agent's Rolodex. Registration ≠ realization — `handoff` decides at runtime which successors are actually summoned. Over-declare freely. |

That is the whole framework surface. Every retry policy, timeout, tracing layer, concurrency limit, persistence strategy, and LLM/tool integration is built by subclassing one of the above — usually in a small handful of lines.

## Patterns that fall out of the primitives

All of the following are expressed with just `takeover` / `handoff` / `>>` / `Flow` inheritance — **no framework feature additions**:

- Sequential pipelines
- Parallel fan-out (one agent → multiple peers in the next layer)
- Fan-in / join (use a Flow's closing rite as the join point)
- Self-loops and reflection (`handoff` returns `self`)
- Conditional routing (rule-based or LLM-decided)
- Hierarchical teams (Flows nested inside Flows; Flows are reusable shared resources)
- Mixed-peer handoff (a single agent and a whole sub-flow running in parallel as peers)
- Dynamic team summoning (construct new agent instances at runtime in `handoff`)
- Scatter-gather over LLM calls (a layer of K parallel callers → a reducer in the next layer)
- Debate / multi-perspective rounds
- Tool-use loops (Reasoner ↔ ToolExecutor handing the baton back and forth)
- Synthesize-then-route in `Flow.handoff` (aggregate the team's output, then decide the next dispatch in one place)
- Cost-tiered routing (rare expensive specialists vs. cheap common workhorses — Pareto distribution is the design goal)

## How BLF differs from other multi-agent frameworks

| Concern | LangGraph | AutoGen | CrewAI | OpenAI Swarm | **BLF** |
|---|---|---|---|---|---|
| Where routing decision lives | Conditional edges (graph-level) | Central GroupChatManager | Process config | Linear handoff (1-to-1) | **Inside each agent's `handoff` (distributed; can be LLM-driven; 1-to-N)** |
| State | TypedDict + reducers | Message lists | Structured Task/Output | Variables | **`Any` — bring your own** |
| Parallel team execution | Available via parallel branches | Limited | Limited | Not native | **Native via tuple-handoff + `AsyncParallelBaseFlow`** |
| Composition model | Subgraphs (must wire into parent) | Group chats | Crews | Linear | **Flow IS Agent → infinite, free composition; Flows are reusable resources** |
| Built-in features | Heavy (state mgmt, checkpoints, viz) | Heavy (messages, roles, memory) | Heavy (roles, processes, memory) | Light | **Minimal — just the protocol; you build the rest by inheritance** |
| Mental model | Graph executor | Actor system with central host | Hierarchical task delegation | Linear baton-pass | **Stewardship-handover protocol; peer collaboration with optional grouping** |

BLF wins when you value: **distributed AI-driven routing**, **free composition**, **opacity (no prescribed schemas)**, **longevity in a fast-moving LLM ecosystem**, and **willingness to subclass for everything**. Other frameworks win when you want **batteries-included features**, **visualization**, **managed durability**, or **out-of-the-box memory/RAG**.

## When BLF is NOT the right tool

- You need a single agent with tools — use a tool-calling library directly.
- You need a static, declarative workflow with rich UI/visualization — use Temporal, Prefect, Airflow, or LangGraph Studio.
- You need durable / resumable execution out of the box — BLF is in-memory by default; you would build persistence on top of `store`.
- You need a managed agent platform with built-in evals, traces, dashboards — use a higher-level product.
- Your team prefers a batteries-included framework with ready-made memory, RAG, and tool registry — BLF deliberately omits these.

## Going deeper

A complete mental-model document lives at [`.claude/skills/branchlayerflow/SKILL.md`](.claude/skills/branchlayerflow/SKILL.md). It captures the design philosophy in depth — eight design pillars (including the meta-principle "convention over enforcement"), vocabulary disambiguation, the two foundational algorithms walked line-by-line, inheritance templates for cross-cutting concerns, an exhaustive pattern catalog, common mistakes, and decision checklists for designing better AI agent systems on top of BLF.

If you use [Claude Code](https://claude.com/claude-code) or another AI coding assistant that recognizes the `.claude/skills/` convention, this skill **auto-loads** when working inside this repository — giving the assistant deep contextual knowledge of how to design idiomatic BLF systems and steering it away from common anti-patterns.

## License

MIT
