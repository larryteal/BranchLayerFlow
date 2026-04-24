---
name: branchlayerflow
description: Use when designing, building, reviewing, refactoring, or explaining multi-AI-agent systems built with the `branchlayerflow` (BLF) Python package — including its base classes BaseAgent / BaseFlow / BaseMeta / AsyncBaseAgent / AsyncBaseFlow / AsyncParallelBaseFlow and its primitives takeover / handoff / successors / store / meta. Triggers when the user mentions BLF, BranchLayerFlow, takeover/handoff/接班/交班 orchestration, the `>>` registration operator, "agent successors" or "agent Rolodex", or asks how to wire multiple LLM agents into sequential pipelines, parallel teams, loops, hierarchical sub-flows, AI-routed dispatch, fan-out / fan-in, scatter-gather, debate, reflection, tool-use loops, or how to add retry / timeout / concurrency limits / observability / persistence on top of BLF. Also use whenever code under review imports from `branchlayerflow`, or when the user asks "how should I structure these agents" / "is BLF the right tool for X" / "what's the difference between BLF and LangGraph / AutoGen / CrewAI / Swarm".
---

# BranchLayerFlow (BLF) — A Mental-Model Skill

> BLF is a deliberately minimal multi-AI-agent collaboration **kernel**. The source is short; the design is dense. This skill exists because reading the code alone does not reveal the philosophy. **Read this first whenever you touch BLF — both before writing code and before explaining it to a human or another AI tool.**

---

## 0. The single most important fact about BLF

**BLF is a framework of base classes meant to be INHERITED, not a library of finished objects meant to be USED.**

Every class is named `BaseXxx`. That naming is a deliberate signal: `BaseAgent`, `BaseFlow`, `BaseMeta`, `AsyncBaseAgent`, `AsyncBaseFlow`, `AsyncParallelBaseFlow` — none of these are intended for direct instantiation as your application's actual building blocks. They are **abstract templates** whose default method bodies are empty (`takeover` is `pass`, `handoff` returns `None`).

The intended usage pattern is:

```python
# WRONG mental model: "I'll use BLF's Agent class"
agent = BaseAgent(meta=...)        # Yes, it works, but does nothing useful

# RIGHT mental model: "I'll inherit from BLF's Base classes to BUILD my agents"
class MyResearcher(BaseAgent):     # ← This is how BLF is meant to be used
    def takeover(self, store): ...
    def handoff(self, store): ...
```

This means BLF is closer to a **protocol + scaffolding** than to a runtime. The framework provides the choreography of stewardship handovers; **your code (your subclasses) IS the application**. The framework does not "run your agents" — it provides the inheritance contract through which your agents collaborate.

**Implication for everything that follows**: when this skill talks about "extending BLF" or "adding retry / observability / etc.", that is not a special advanced feature — that is **the normal way you use BLF**. There is no other way.

---

## 1. The one-paragraph essence

BLF is a **stewardship-handover protocol for AI agents**, expressed as a small inheritance hierarchy. Each Agent (your subclass of `BaseAgent`) `takeover`s a piece of in-flight work — reading the shared `store`, contributing its specialty — then `handoff`s to one or more next stewards (returning a `Tuple[BaseAgent, ...]`). A `Flow` (your subclass of `BaseFlow`) is the conversational scope (a "meeting room") that schedules its contained branches **layer by layer with synchronization barriers between layers**, and itself acts as the "last speaker" of that scope when all its branches have terminated. Because `BaseFlow(BaseAgent)`, every Flow is itself an Agent — so the same dispatch primitive composes infinitely. The framework is silent about LLM clients, tools, prompts, retries, observability, persistence, and validation — those are all expected to live in your subclass overrides or in the shape of your `store`.

---

## 2. The framework's complete contract — four things you must provide

The entire surface BLF requires from your code:

| What | Where | Notes |
|---|---|---|
| **`meta.name : str`** | A `BaseMeta` subclass instance per Agent | The framework reads ONLY this field. Required because successors are dict-keyed by name. |
| **`takeover(store) -> None`** | Override in your `BaseAgent` subclass | Do your part of the work. Mutate `store`. Defaults to `pass`. |
| **`handoff(store) -> Optional[Tuple[BaseAgent, ...]]`** | Override in your `BaseAgent` subclass | Decide who takes the next shift. Defaults to `None` (== `()`, branch terminates). |
| **`store : Any`** | Caller-defined object | Whatever shape your domain needs. Framework treats it as fully opaque. |

Everything else — LLM provider, prompt format, tool registry, message schema, retry policy, timeout, rate limit, tracing, persistence, validation, evaluation harness — is **explicitly outside the framework's scope**, by design. If you ever feel the urge to extend BLF to support feature "X", the answer is almost always:

> "X belongs in user code: in a subclass of one of the existing classes, or in the shape of `store`, or in fields you add to your Meta subclass."

This is not a limitation. It is the source of BLF's longevity — see Section 8 (framework opacity).

---

## 3. Vocabulary — the words BLF uses are loaded; do not flatten them

Every term in BLF was chosen carefully. Misreading any of them produces wrong mental models that lead to bad designs. **When you or another AI tool starts using the LHS column words, stop and re-read this table.**

| BLF term | What it does NOT mean | What it DOES mean |
|---|---|---|
| **Agent** | A long-lived service / persistent worker / actor | A *short-lived stewardship*: each invocation is one shift — pick up the in-flight work, contribute, hand off, exit. The same Agent instance invoked twice = two separate shifts. |
| **takeover** | "execute / process / handle / run" | *"I'm taking over from where things are; I do my piece"* — like a doctor receiving a patient at shift change, a worker stepping onto a production line, a relay runner accepting the baton. |
| **handoff** | "return value / next node / route to / dispatch" | *"I'm done; here is my recommendation for who takes the next shift"* — relay-race baton-pass. The giver is **finished**; control does NOT come back to them. |
| **Flow** | A workflow definition / static graph / DAG | A **meeting scope** that opens at `takeover` (opening rite), schedules its branches layer-by-layer in between, and closes at `handoff` (closing rite — the team's last word). It is itself an Agent, so it can be a peer participant in any other scope. |
| **Branch** | A graph edge | A *currently-in-flight stewardship* — a unit of live concurrency. `n_branches` is the live count. |
| **Layer** | A graph level | A *synchronized round* — a barrier; every branch in the round must produce its successors before the next round forms. |
| **store** | Framework state / typed schema / message buffer | An *opaque shared workspace* the framework refuses to inspect. You bring your own data model — dict, pydantic model, ORM session, event bus, anything. The framework only pipes the same reference through every invocation. |
| **meta** | Generic metadata bag | A frozen *business card*. Only `name` is read by the framework (for the successors dict key). Everything else (role, capabilities, model, cost tier, prompt template, tags) is **your description for AI-driven dispatchers to read** when choosing teammates. |
| **successors** | "Out-edges" / next-step list | A *Rolodex / address book / capability radius* — declared possibilities, not realized paths. Over-declare freely. |
| **`>>` operator** | "Connect / chain / wire the graph" | *"Add this person to my Rolodex"* — does not imply this person will ever actually be called. |
| **`>>` + `handoff`** | A graph edge with a condition | **Two completely separate concerns**: `>>` declares a possibility (static registration), `handoff` realizes a runtime choice (often via an LLM call). Do not collapse them. |
| **`parent_flow`** | A boss / parent in an org chart | An *accounting back-pointer* set dynamically when an agent gets dispatched. Used only for completion bookkeeping (decrementing `n_branches` and bubbling up). It implies no command authority. |
| **`Base*` class names** | Default implementations you instantiate | *Abstract templates* you inherit from. Direct instantiation runs no useful logic. |

---

## 4. The verb-centric collaboration model — why takeover/handoff matter

Compare the core verbs of multi-agent frameworks:

| Framework | Core verbs | Implied mental model |
|---|---|---|
| LangGraph | `add_node` / `add_edge` / `invoke` | Computational graph execution |
| AutoGen | `send` / `receive` / `generate_reply` | Actor message passing |
| CrewAI | `kickoff` / `delegate` / `execute_task` | Hierarchical task delegation |
| OpenAI Swarm | `run` / `handoff` (1-to-1 only) | Linear baton-pass |
| **BLF** | **`takeover` / `handoff`** | **Shift-based stewardship collaboration** |

BLF is the only framework here whose core verbs are **not engineering verbs** at all — they are taken from the vocabulary of human work handovers (hospital shift change, military command transfer, relay race, customer-service escalation, manufacturing-line workpiece transfer). This is deliberate.

**The implication**: complex AI tasks are not single computations — they are **sequences of stewardships**, each handler doing the part it is qualified for, then yielding to whoever should handle the next part. This is how complex human work actually flows:

| Domain | Stewardship chain |
|---|---|
| Hospital | ER → Imaging → Specialist consult → ICU → Surgery → Recovery → Outpatient |
| Manufacturing | Cut → Weld → Paint → QA (loop back if defect) |
| Customer support | Tier 1 → Tier 2 → Engineering → SRE → Postmortem |
| Software delivery | PM → Designer → Engineer → Code review → QA → Canary → Rollout |
| Research | Literature → Experiment → Writing → Peer review → Revision |

Common property: **none of these can be done by a single specialist**. The complexity is in the **coordination** — knowing when to take over, what to contribute, when and to whom to hand off — not in any single step.

**BLF assumes your AI work is the same shape**. Don't build a giant agent that does everything; build small specialists that:
1. Recognize when they should take over (their meta/role matches what the situation calls for)
2. Do exactly their part (inside `takeover`)
3. Recognize when their stewardship is complete (handoff returns `()`) or who should continue (`handoff` returns the right teammate(s))

The framework provides the **collaboration protocol**; your subclasses provide the **specialists**.

### A consequence: an Agent's life is one shift

Read `_iter`:

```python
def _iter(self, store):
    self._takeover(store)             # I take over
    yield self._handoff(store) or ()  # I hand off (or terminate); I exit
```

That is the entire lifecycle. The Agent does not "exist between calls". Even if the same Agent instance is invoked again later (by a loop, by another flow), each invocation is a **fresh shift**. There is no persistent "agent process" to think about — only **shift episodes**.

---

## 5. The eight design pillars

These are the load-bearing ideas. Every BLF pattern, every override, every design decision should respect them. **If a proposed extension violates one, it almost certainly fights the framework.**

### Pillar 1 — Inheritance IS the usage pattern; cross-cutting concerns are subclasses

Look at the method pairs: `takeover` / `_takeover`, `handoff` / `_handoff`. The framework calls the underscore-prefixed form; you write the no-underscore form. **This double-layer is a deliberate aspect-orientation seam.**

| Where to put what |
|---|
| **Business logic** (your domain work, your LLM call, your tool use) → `takeover` / `handoff` |
| **Cross-cutting concerns** (retry, timeout, tracing, caching, rate limit, error containment) → override `_takeover` / `_handoff` to wrap your business code |

Standard recipes — these are not "plugins" or "framework features", they are how you USE the framework:

```python
# Retry (sync)
class RetryAgent(BaseAgent):
    def _takeover(self, store):
        for i in range(self.meta.max_retries):
            try: return self.takeover(store)
            except Exception:
                if i == self.meta.max_retries - 1: raise

# Timeout (async)
class TimeoutAsyncAgent(AsyncBaseAgent):
    async def _takeover(self, store):
        await asyncio.wait_for(self.takeover(store), timeout=self.meta.timeout)

# Tracing
class TracedAgent(BaseAgent):
    def _takeover(self, store):
        with tracer.start_as_current_span(self.meta.name):
            return self.takeover(store)
```

Other extension seams (in order of how often they're useful):

- `_get_successors` (Flow) — per-agent dispatch wrapper. Right place for **per-agent error containment**, **per-agent retry**, **per-agent skip-conditions**.
- `_next_layer_successors` (Flow) — layer-level scheduler. Right place for **concurrency limits, bulkheads, priority scheduling, fairness**. (`AsyncParallelBaseFlow` itself is just an override of this seam — `gather` instead of sequential await.)
- `_iter` (Agent or Flow) — full execution loop. Rare; use to change yield protocol or insert global lifecycle.
- `__rshift__` — change what `>>` means in your subclass (e.g., enforce types, add weights, prevent duplicate registration).
- `BaseMeta` subclass — add any fields you want for declarative agent configuration.

The result: every "missing feature" you can think of (retry, timeout, concurrency limit, observability, persistence, error isolation) is a **small subclass**, not a framework gap. The framework refuses to bake them in because **what's needed varies per project** and **the right approach changes faster than framework releases**.

### Pillar 2 — Static declaration ≠ dynamic realization (Rolodex + AI dispatch)

`a >> b` registers `b` in `a.successors` (a dict keyed by `b.meta.name`). It does NOT say `b` will ever run.

`handoff(store)` is what actually decides — at runtime, in user code, possibly via an LLM call — which 0-to-N successors get the floor.

**These are two completely separate concerns**:

```python
# Static registration — declare possibilities (your Rolodex)
reviewer >> security_expert
reviewer >> performance_expert
reviewer >> accessibility_expert
reviewer >> testing_expert
reviewer >> docs_expert
reviewer >> human_escalation   # rare safety-net successor

# Dynamic realization — AI picks who to actually summon for THIS situation
class CodeReviewer(BaseAgent):
    def handoff(self, store):
        candidates = [
            {"name": a.meta.name, **a.meta.model_dump(exclude={"name"})}
            for a in self.successors.values()
        ]
        decision = llm.choose_teammates(situation=store, candidates=candidates)
        return tuple(self.successors[n] for n in decision.chosen_names)
```

Implications you must internalize:

- **Over-declare freely.** Registering an unused successor costs nothing. Your Rolodex represents your competence radius ("who I know how to escalate to / collaborate with"), not your execution path.

- **Pareto distribution is the design goal, not a bug.** In a healthy BLF system: ~20% of successors handle ~80% of dispatches; long-tail specialists fire rarely but critically. Some successors might never fire in a given run yet be essential for safety. This mirrors real organizations: most cases handled by a few generalists, rare cases routed to specialists. Treat actual frequency distribution as a **runtime diagnostic** — if a "should be common" agent rarely fires, your routing is wrong; if a rare specialist fires often, the upstream is misjudging.

- **Topology emerges per run.** Same agents, same `>>` wiring, completely different paths depending on store state. You are not designing a graph; you are designing a **set of locally-intelligent dispatchers** whose collective decisions produce a graph at runtime.

- **Subsidiarity (decisions at the lowest competent level).** Each Agent's `handoff` knows its own domain best — no central scheduler can match. The "code reviewer" is the right thing to decide whether this PR needs the security expert; not a top-level orchestrator. **Routing knowledge is distributed across agents.**

### Pillar 3 — Layer barriers = structural concurrency for free (BSP applied to AI agents)

Within a Flow, agents at the same depth run as a "layer". The barrier is built into `_next_layer_successors`: the next layer is computed only after **all** current-layer agents have produced their successors. Branches in the same layer **never see each other** during their turn — they only communicate through `store` (which the next layer reads).

This is **Bulk Synchronous Parallel (BSP) — Pregel applied to LLM agents**:

| BSP / Pregel | BranchLayerFlow |
|---|---|
| Vertex | Agent |
| Superstep | Layer |
| Active vertex set | `n_branches` worklist counter |
| compute → message → barrier | takeover → handoff → next-layer-resolve |
| Message passing | through `store` |
| Halt vote | `handoff` returns `()` |

BSP was the model behind distributed graph processing (Pregel, Giraph) precisely because it makes parallelism reasonable: **you don't need locks, channels, or futures to coordinate** — the layer boundary IS the synchronization primitive.

The 2D parallelism matrix that BLF supports:

| Class | Within a layer | Across layers |
|---|---|---|
| `BaseFlow` | sequential `for`-loop | sequential |
| `AsyncBaseFlow` | sequential `await` | sequential |
| `AsyncParallelBaseFlow` | `asyncio.gather` (truly parallel) | sequential (barrier always in place) |

**The cross-layer dimension stays sequential no matter what scheduler you pick** — the BSP barrier guarantee is preserved by every Flow class. That's why parallelism is safe-by-construction.

`AsyncParallelBaseFlow` differs from `AsyncBaseFlow` by exactly one line — replacing the comprehension with `gather`. This works because:

- Same-layer branches don't see each other ⇒ `gather` cannot create logical races
- Layer barrier is built-in ⇒ no need for explicit futures
- Per-agent successor computation is independent ⇒ slicing is trivial
- `sum(successors, ())` (the per-layer flatten) is **associative and commutative** ⇒ ordering doesn't matter

**Practical implication**: do not invent your own synchronization primitives. Place agents you want to "join" in the same layer; the next layer is automatically the join point. Place agents you want sequential in adjacent layers. To add concurrency limits, override `_next_layer_successors` and wrap with `Semaphore`; the barrier semantics stay intact.

### Pillar 4 — Flow IS Agent → composition is free; no "sub-" type distinction

`BaseFlow(BaseAgent)`. The `handoff` signature is `Tuple[BaseAgent, ...]`. Therefore:

```python
class Strategist(BaseAgent):
    def handoff(self, store):
        return (
            single_critic_agent,        # individual peer
            research_team_flow,          # whole sub-team brought as one peer
            self,                        # myself again (loop)
            agent_from_another_team,     # cross-team peer
        )
```

All four are **type-equivalent at the dispatch site**. The dispatcher does not know or care whether a returned member is a single Agent or a whole Flow with its own internal multi-layer execution. **Liskov substitution is fully honored.**

This means several things that other multi-agent frameworks struggle to express:

- **Mixed-peer handoff**: an Agent and a Flow can stand at the same layer as peers (one runs solo; one expands into its own sub-conversation; both barrier together at the next layer).
- **Flow returned from handoff is NOT a "subroutine call"**. Control does NOT "come back" to the caller. The Flow takes its turn as a peer and the conversation continues from wherever its handoff (closing rite) lands.
- **No artificial "agent dispatcher" vs "flow dispatcher" distinction** in your design. You write one `handoff`; what it returns can be any mixture.
- **A Flow can be a peer in another team without being its child.** Because `parent_flow` is dynamic accounting (Pillar 5), Flows are reusable shared resources — like conference rooms in an office building, not departments.

This unlocks **inverted hierarchies**: a "manager" Agent can hand off to a "specialist" Flow. The manager is just a coordinator; the specialist team does the substantive work. The "manager" has no authority over the team — it merely invited them to take their turn.

### Pillar 5 — `parent_flow` is accounting, not authority

Every Agent has a `parent_flow` back-pointer, set/reset dynamically when the agent gets dispatched (look at `_get_successors`). This pointer exists for **one purpose only**: completion bookkeeping.

When a branch returns `()`, the framework decrements its parent flow's `n_branches`. When that hits zero AND the branch produced no successors, the framework calls the parent flow's own `handoff` — if THAT also returns `()`, it bubbles up to the grandparent, and so on:

```python
while not successors and flow.n_branches <= 0 and flow.parent_flow:
    successors = flow._handoff(store) or ()
    flow = flow.parent_flow
```

This is the only place `parent_flow` is used. It is **completion-tracking infrastructure**, not an org-chart relationship.

The deep consequence:

- **A Flow does NOT command its branches.** Flow.takeover does not "tell agents what to do"; it just opens the scope. Branches decide their own next steps via their own `handoff`.
- **The Flow looks like a "leader" only when an agent inside it looks UP.** From outside (other agents handing off TO the Flow), the Flow is just another peer-participant.
- **Authority and accounting are different concepts.** BLF deliberately has only the latter, never the former.

This is why BLF's collaboration model is **peer-collaboration with optional grouping**, not **hierarchical control**:

| Closer to | Further from |
|---|---|
| Self-organizing teams (Agile / Holacracy) | Org charts |
| Conference call dynamics (anyone can yield to anyone, breakouts exist but aren't authority) | Workflow engines (explicit step ownership) |
| Erlang Actor + structured concurrency | Master-worker patterns (authority asymmetry) |
| Academic seminars (anyone can invite anyone) | Approval chains |

When you design with BLF, the question is never "what is my org chart?" The question is "**given this state, who is the right peer to invite next?**" The collaboration shape **emerges** from a sequence of local handoff decisions.

### Pillar 6 — Flow's `takeover` and `handoff` bracket the entire team's work — and the closing rite is where supervision (and often synthesis) actually happens

Re-read Flow's `_iter`:

```python
def _iter(self, store):
    self._takeover(store)                      # OPEN the scope (opening rite — once at start)
    layer_successors = self.branches
    yield layer_successors
    while layer_successors:
        layer_successors = self._next_layer_successors(store, layer_successors)
        if layer_successors:
            yield layer_successors
    yield self._handoff(store) or ()           # CLOSE the scope (closing rite — last word)
```

A Flow's `takeover` and `handoff` are **temporally separated by the entire team's work**. takeover happens once at start; handoff happens after every branch in the scope has terminated. By the time `handoff` is called, `store` contains the **cumulative output of the entire team**.

This is the moment where the Flow becomes uniquely powerful. It is the only entity in the scope that sees the **collective artifact**. Its `handoff` is the **team's collective continuation decision**. It can:

| Strategy | Handoff returns |
|---|---|
| **Truly close** | `()` — the scope is genuinely done; bubble up |
| **Deliver / wrap up** | `(deliverable_agent,)` — pass to a single closing agent that publishes / formats / persists |
| **Re-do whole round** | `self.branches` — quality not met, run the team again |
| **Re-do partial round** | a subset of `self.branches` — only some agents need another pass |
| **Pivot** | new agents not in `self.branches` — direction change based on results |
| **Escalate / scale up** | a more powerful sub-flow — task turned out harder than expected |
| **Bubble up to outer** | `()` — let the parent flow's handoff decide next move |

**Crucially, this decision can itself be an LLM call** that reads `store`. That means:

- **Flow becomes "emergent supervision"** — it doesn't supervise during the team's work (no commands during execution), only at the closing rite (after the dust settles).
- **Quality gates, retry-until-good-enough, pivot-on-failure, and human-in-the-loop checkpoints** all live naturally in `Flow.handoff`.
- **The scope's strategy can adapt per run** — the Flow looks at what its team produced and decides what kind of follow-up the situation calls for.

**Equally important: `Flow.handoff` is also a legitimate place to DO WORK, not only to route.** The closing rite is the unique moment where:
- The team's cumulative output is fully settled in `store` (every branch terminated, layer barriers all cleared)
- The next dispatch decision is about to be made

If the next dispatch logically depends on a **synthesis / summary / aggregation** of what the team produced, that synthesis must happen here — because it must precede the dispatch decision and there is no later opportunity. You *could* offload it to a "synthesizer" agent placed as a final layer, but that costs an extra layer of latency, splits one logical decision across two agents, and the synthesizer cannot itself perform the Flow-level dispatch. Doing both in `Flow.handoff` is often cleaner:

```python
class ResearchFlow(BaseFlow):
    def handoff(self, store):
        # SYNTHESIS — work that must precede the dispatch decision
        store["summary"] = synthesize(store["raw_findings"])
        store["confidence"] = score(store["summary"])

        # ROUTING — based on the just-computed synthesis
        if store["confidence"] < 0.7:
            return self.branches                          # rerun the team
        if store["confidence"] > 0.95:
            return (self.successors["publisher"],)
        return (self.successors["reviewer"],)
```

When designing, treat Flow.handoff as the **strategic decision point of that scope** — equal in importance to its branches' work, and often the right place to put the team's "summary processing" too. (See Pillar 8 for the broader principle.)

### Pillar 7 — Framework opacity is deliberate non-prescription (the kernel/userland split)

The framework refuses to know about:

- LLM clients, providers, models, prompts
- Tool calling protocols
- Memory / RAG abstractions
- Message formats
- Retry / timeout / circuit-breaker policies
- Observability / tracing
- Persistence / checkpointing
- Validation / schema
- Evaluation harnesses

`store: Any` and `BaseMeta` with `extra="allow"` are how this opacity is implemented. The framework propagates `store` reference through every invocation and reads only `meta.name` — nothing else.

This is **maximum delegation**:

| BLF type | Effect |
|---|---|
| `store: Any` | You bring your own data model (dict / pydantic / ORM session / event bus / object with locks). Framework refuses to inspect, validate, persist, or log. |
| `BaseMeta` with `extra="allow"` and `frozen=True` | You add any fields you want. Framework reads only `name`. The other fields become your agent's **business card** — what an AI dispatcher reads to decide whom to invite. |

Why this is right for the LLM era:

| What's stable (in the framework) | What's changing (in your code) |
|---|---|
| Collaboration choreography (takeover/handoff) | Which LLM, which prompt, which model version |
| Layer barrier + branch counting | Tool calling protocols |
| Flow IS Agent (algebraic closure) | Memory abstractions, RAG techniques |
| Two-step dispatch (Rolodex + handoff) | Retry / observability / persistence patterns |

The LLM ecosystem changes every few months. **BLF deliberately keeps only the timeless protocol in the framework, and pushes everything fast-changing into user code.** This is why the framework can age well: it commits to the things that don't go out of fashion.

This is **the Unix philosophy applied to multi-agent systems**:

| Unix philosophy | BLF correspondence |
|---|---|
| Do one thing well | Only collaboration choreography |
| Compose with everything else | Opaque `store` and extensible `meta` are the universal interfaces |
| Mechanism, not policy | Provides takeover/handoff mechanism; doesn't dictate policy on retry, observability, etc. |
| Kernel vs userland | BLF is the kernel; your subclasses + LLM client + tools + memory are userland |

**BLF is the kernel of multi-agent systems.** Treat it accordingly.

### Pillar 8 — Convention over enforcement: 法无禁止即可为 ("what is not forbidden is permitted")

This is a meta-pillar that qualifies all the others. **Distinguish carefully between what the framework actually enforces and what is merely good practice.**

What the framework genuinely enforces (mechanical constraints):
- `meta.name` must be a string (because successors are dict-keyed by it)
- `handoff` must return `Optional[Tuple[BaseAgent, ...]]` (the dispatcher reads this)
- `parent_flow` accounting is internal — don't poke it

That is essentially the entire enforced contract. Everything else in this skill — including:
- "do work in `takeover`, dispatch in `handoff`"
- "business logic in `takeover`/`handoff`, cross-cutting in `_takeover`/`_handoff`"
- "Flow's `takeover` is just an opening rite"
- "agent attributes are for `successors`, state goes in `store`"
- "Meta is a business card, not state"

— is **convention and best practice, not framework law**. The framework will gladly run code that departs from these conventions. **When you have a justified reason, deliberate departures are fine.**

Common legitimate departures:

1. **Doing substantive work in `Flow.handoff`** (synthesis-then-route). Already covered in Pillar 6 — this is the canonical "you can only do it here" case.

2. **Doing a small computation in an Agent's `handoff` to inform routing.** If your dispatch decision needs to compute an aggregate or apply a rule that doesn't make sense in `takeover`, putting that small computation in `handoff` is fine. The convention "`takeover` is for substantive work, `handoff` is for routing" doesn't mean "`handoff` must be pure".

3. **A pure-routing Agent with empty `takeover`.** Sometimes an Agent exists only to make a routing decision (a "pure router"). Its `takeover` is `pass` and all the logic is in `handoff`. Perfectly fine.

4. **Reading `store` in `_takeover` / `_handoff` overrides for cross-cutting decisions.** E.g., a `RetryAgent` whose retry count varies per call based on store state. Cross-cutting code can read store; it just shouldn't contain business logic.

5. **Mutating `meta`-like config in `store`** when truly per-run configuration changes are needed (e.g., model selection per run). Meta itself stays frozen; the dynamic part lives in store.

The right mental rule:

> **Treat the conventions as the default that keeps code clean and reasoning simple. Treat the framework's actual enforcement as the only hard line. When the situation makes a convention more painful than helpful — and you can articulate why — go ahead and depart.**

Most of the time the conventions are right and you should follow them by reflex. But the framework respects your judgment when the design genuinely needs an exception. **法无禁止即可为** is not permission to be sloppy; it is permission to be precise when precision requires breaking a default.

---

## 6. The two foundational algorithms (read these to understand the framework)

### 6.1 The branch-counting worklist (the layer barrier and bubble-up)

```python
def _get_successors(self, store, agent):
    agent_iter = agent(store)
    successors = agent_iter.__next__()       # take exactly ONE batch from the agent
    agent_iter.close()                        # then close — agent does its shift and exits

    flow = agent if isinstance(agent, BaseFlow) else agent.parent_flow

    if isinstance(agent, BaseFlow):
        flow.n_branches = len(successors)     # a sub-flow finishing resets count
    else:
        flow.n_branches += len(successors) - 1
        # ↑ THE central algebra: each agent execution closes 1 slot and opens N slots
        # → net change is N - 1. When the counter drains to 0, the team is done.

    # Bubble up: when our flow has no live branches, ask its handoff (closing rite)
    while not successors and flow.n_branches <= 0 and flow.parent_flow:
        successors = flow._handoff(store) or ()
        flow = flow.parent_flow
        flow.n_branches += len(successors) - 1

    # Re-parent successors (dynamic accounting; respects in-use Flows)
    for successor in successors:
        if not isinstance(successor, BaseFlow) or (
            successor.n_branches <= 0 or successor.parent_flow is None
        ):
            successor.parent_flow = flow

    return successors
```

Three things to internalize:

1. **`flow.n_branches += len(successors) - 1`** is the entire concurrency model in one expression. It is the worklist counter for "live stewardships in this scope".
2. **The bubble-up `while`** is how Flow's "closing rite" works structurally. It is the mechanism by which a sub-conversation ending naturally returns the floor to the outer conversation.
3. **The re-parenting condition** prevents Flow hijacking — a Flow currently in use (with active branches) won't be claimed by a new parent, but a fresh or exhausted Flow can be reused. This is what makes Flows shareable resources.

### 6.2 The layer walker (BFS with barrier + opening/closing rites)

```python
def _iter(self, store):
    self._takeover(store)                      # OPENING RITE — once at start
    layer_successors = self.branches           # initial layer = the team
    yield layer_successors
    while layer_successors:
        layer_successors = self._next_layer_successors(store, layer_successors)
        if layer_successors:
            yield layer_successors             # one yield per round (layer barrier)
    yield self._handoff(store) or ()           # CLOSING RITE — last word after team exhausts
```

The yields are the natural observation points: each yield is one synchronized round. Whoever drains the generator (your runner code) sees the meeting unfold round-by-round, and can drop logging, tracing, or human approval between yields without modifying the framework.

---

## 7. The minimum-viable inheritance templates

Always start from these. **Replace the bodies; do not change the shape.** All BLF applications are essentially elaborations of these templates.

### 7.1 Custom Meta (your agent's "business card")

```python
class MyMeta(BaseMeta):
    # framework reads only `name`; everything below is for YOUR code:
    # — for AI-driven `handoff` to read when picking teammates
    # — for cross-cutting `_takeover` overrides to read for retry/timeout/etc.
    role: str = ""
    description: str = ""
    capabilities: list[str] = []
    cost_tier: str = "standard"           # for cost-aware routing
    model: str = ""                        # which LLM to use
    prompt_template: str = ""              # this agent's system prompt
    max_retries: int = 1                   # for RetryAgent subclass
    timeout_s: float | None = None         # for TimeoutAgent subclass
```

`extra="allow"` is set on `BaseMeta`, so you can also add fields ad-hoc. `frozen=True` is set, so identity stays stable across the agent's lifetime — necessary for dispatch decisions to remain valid.

### 7.2 Custom Agent

```python
class MyAgent(BaseAgent):
    def takeover(self, store):
        # Default home for substantive work: read in-flight state from store,
        # contribute YOUR specialty, mutate store with your output.
        # Routing decisions normally go in `handoff` (cleaner separation),
        # but the framework doesn't enforce this — see Pillar 8.
        ...

    def handoff(self, store):
        # Primary purpose: decide WHO comes next from your Rolodex.
        # Return:
        #   (agent_a,)                           — pass to single agent
        #   (agent_a, agent_b, agent_c)          — pass to parallel team
        #   (sub_flow,)                          — pass to a whole sub-team
        #   (agent_a, sub_flow_b)                — mixed peers, all in next layer
        #   (self,)                              — loop / self-reflection
        #   ()                                   — this branch's stewardship is complete
        #   None                                 — same as ()
        # Natural place to put an LLM call that picks teammates.
        # Small computations needed to inform routing are fine here too (Pillar 8).
        return (self.successors["next_role"],)
```

### 7.3 Custom Flow

```python
class MyFlow(BaseFlow):
    def takeover(self, store):
        # OPENING RITE — called ONCE at start of this scope.
        # Do scope-level setup: initialize working memory, log scope start, etc.
        ...

    def handoff(self, store):
        # CLOSING RITE — called AFTER every branch in this scope has terminated.
        # store now contains the team's COMPLETE collective output.
        #
        # This method has two legitimate jobs (often both at once — see Pillar 6):
        #
        # (a) SYNTHESIS / aggregation of the team's output (work that MUST happen
        #     here because it must precede the dispatch decision and there's no
        #     later opportunity within this scope):
        #         store["summary"] = synthesize(store["raw_outputs"])
        #
        # (b) ROUTING / supervision decision based on that synthesis:
        #         ()                        — scope truly done
        #         (delivery_agent,)         — pass to a closing agent
        #         self.branches             — re-run the same team (loop)
        #         (different_team_flow,)    — pivot
        #         (escalation_flow,)        — escalate
        #
        # The routing decision itself can be an LLM call ("supervisor judgment").
        ...
```

### 7.4 Cross-cutting concerns — also inheritance

```python
# Per-agent retry
class RetryAgent(BaseAgent):
    def _takeover(self, store):
        for i in range(self.meta.max_retries):
            try: return self.takeover(store)
            except Exception:
                if i == self.meta.max_retries - 1: raise

# Per-agent timeout (async)
class TimeoutAsyncAgent(AsyncBaseAgent):
    async def _takeover(self, store):
        await asyncio.wait_for(self.takeover(store), timeout=self.meta.timeout_s)

# Per-agent error containment (Flow side — keeps other branches alive)
class ResilientFlow(AsyncParallelBaseFlow):
    async def _get_successors(self, store, agent):
        try:
            return await super()._get_successors(store, agent)
        except Exception as e:
            store.setdefault("errors", []).append({"agent": agent.meta.name, "error": str(e)})
            return ()                          # this branch dies; siblings continue

# Concurrency limit per layer
class BoundedParallelFlow(AsyncParallelBaseFlow):
    async def _next_layer_successors(self, store, layer):
        sem = asyncio.Semaphore(self.meta.max_concurrent)
        async def guarded(a):
            async with sem:
                return await self._get_successors(store, a)
        results = await asyncio.gather(*(guarded(a) for a in layer))
        return sum(results, ())

# Tracing every agent invocation
class TracedAgent(AsyncBaseAgent):
    async def _takeover(self, store):
        with tracer.start_as_current_span(self.meta.name):
            return await self.takeover(store)
```

These mixins compose: subclass `RetryAgent` AND `TracedAgent` to get both. Stack `BoundedParallelFlow` as the outer Flow and `ResilientFlow` as inner. **Cross-cutting concerns are normal Python inheritance — no framework features needed.**

### 7.5 Running the flow (drainage convention)

The Flow's `__call__` returns a generator that yields **one tuple per layer**.

```python
# Sync — discard yields, just execute
from collections import deque
deque(master_flow(store=store), maxlen=0)

# Sync — step through layers (e.g., to log / trace / pause for HITL)
for layer in master_flow(store=store):
    log(f"layer with {len(layer)} branches: {[a.meta.name for a in layer]}")

# Async
async for layer in master_flow(store=store):
    pass

# HITL pause point — drop human approval between layers
async for layer in master_flow(store=store):
    if needs_human_approval(layer):
        await human.approve(store)
```

---

## 8. Pattern catalog (idioms that fall out of the primitives)

Each of these is implemented purely with `takeover` / `handoff` / `>>` / Flow inheritance — **no framework feature added**. When asked "how do I do X in BLF?", check this list.

### Sequential pipeline (A → B → C)

```python
class A(BaseAgent):
    def handoff(self, store): return (self.successors["b"],)
# similarly B, C
a >> b >> c
flow = MyFlow(meta=..., branches=(a,))
```

### Parallel fan-out (A → {B, C, D in parallel})

```python
class A(BaseAgent):
    def handoff(self, store):
        return (self.successors["b"], self.successors["c"], self.successors["d"])
a >> b; a >> c; a >> d
flow = MyAsyncParallelFlow(meta=..., branches=(a,))
```

### Fan-in / Join (B, C, D → E)

The cleanest pattern: enclose B/C/D in a Flow whose `handoff` returns `(e,)` after they all terminate. The closing rite of the inner Flow IS the join point.

### Self-loop / Reflection

```python
class Reasoner(BaseAgent):
    def handoff(self, store):
        if store["confidence"] < 0.8:
            return (self,)                      # call myself again on next layer
        return (self.successors["finalizer"],)
```

### Loop-until-condition (Flow-level)

```python
class IterativeFlow(BaseFlow):
    def handoff(self, store):
        if store["quality"] < 0.9 and store["iters"] < 5:
            store["iters"] += 1
            return self.branches                # re-run the same team
        return ()                                # done
```

### AI-driven router (the canonical pattern for LLM systems)

```python
class Router(BaseAgent):
    def handoff(self, store):
        decision = llm.choose(
            situation=store,
            candidates=[
                {"name": a.meta.name, **a.meta.model_dump(exclude={"name"})}
                for a in self.successors.values()
            ],
        )
        return tuple(self.successors[n] for n in decision.chosen_names)
```

### Hierarchical team (Flow nested in Flow)

```python
research_team = ResearchFlow(meta=..., branches=(searcher, summarizer))
writing_team  = WritingFlow(meta=..., branches=(drafter, editor))
research_team >> writing_team                   # research's closing rite hands off to writing
master = MasterFlow(meta=..., branches=(research_team,))
```

### Mixed-peer handoff (Agent + Flow in parallel)

```python
class Strategist(BaseAgent):
    def handoff(self, store):
        return (
            self.successors["solo_critic"],     # individual peer
            self.successors["research_team"],   # whole team peer
        )
# Both run as branches of the same layer; layer barrier waits for BOTH.
```

### Dynamic team summoning (runtime-constructed agents)

```python
class Dispatcher(BaseAgent):
    def handoff(self, store):
        team = tuple(
            SpecialistAgent(meta=MyMeta(name=f"specialist_{i}", **specs))
            for i, specs in enumerate(store["needed_specialists"])
        )
        return team
```

### Scatter-gather (K parallel LLM calls → 1 reducer)

```python
class ScatterFlow(AsyncParallelBaseFlow):
    def handoff(self, store):
        return (self.successors["reducer"],)    # closing rite passes to reducer
# branches=(caller_1, caller_2, ..., caller_k) — all run in parallel via gather
# layer barrier waits for all K to finish, reducer sees all results in store
```

### Debate / multi-perspective

```python
class Moderator(BaseAgent):
    def handoff(self, store):
        if store["rounds"] < 3 and not store["consensus"]:
            store["rounds"] += 1
            return (self.successors["proponent"], self.successors["critic"])
        return (self.successors["synthesizer"],)
```

### Tool-use loop

```python
class Reasoner(BaseAgent):
    def handoff(self, store):
        if store["pending_tool_call"]:
            return (self.successors["tool_executor"],)
        if store["needs_more_thought"]:
            return (self,)
        return ()                                # truly done

class ToolExecutor(BaseAgent):
    def handoff(self, store):
        return (self.successors["reasoner"],)    # always hand back to the reasoner
```

### Synthesize-then-route in Flow.handoff (the closing-rite work pattern)

When the next dispatch decision depends on a synthesis of the team's output, do BOTH in `Flow.handoff`. Saves a layer; keeps "synthesize and decide" as one logical step (Pillar 6 / Pillar 8).

```python
class IterativeResearchFlow(BaseFlow):
    def handoff(self, store):
        # SYNTHESIS work — must precede the routing decision
        store["synthesis"] = synthesize(store["raw_findings"])
        score = quality_score(store["synthesis"])

        # ROUTING based on the just-computed synthesis
        store["iters"] = store.get("iters", 0) + 1
        if score >= 0.9:
            return (self.successors["delivery"],)
        if store["iters"] < 5:
            return self.branches               # rerun the team with synthesis context
        return (self.successors["escalate_to_human"],)
```

### Cost-tiered routing (rare expensive specialist)

```python
class CostAwareRouter(BaseAgent):
    def handoff(self, store):
        if store["complexity"] > 0.8:
            return (self.successors["opus_expert"],)     # rare expensive
        return (self.successors["haiku_worker"],)         # common cheap
```

---

## 9. Comparison with other multi-agent frameworks (use this when explaining BLF)

| Concern | LangGraph | AutoGen | CrewAI | OpenAI Swarm | **BLF** |
|---|---|---|---|---|---|
| **Routing decision lives** | In conditional edges (graph-level, deterministic) | In a central GroupChatManager (centralized LLM dispatcher) | In Process config (preset hierarchical / sequential) | In handoff (1-to-1) | **In each Agent's `handoff` (distributed, can be LLM-driven, 1-to-N)** |
| **State** | TypedDict + reducers (prescribed) | Message lists (prescribed) | Structured Task/Output (prescribed) | Variables (prescribed) | **`Any` (you bring your own)** |
| **Parallel team execution** | Possible via parallel branches in graph | Limited (sequential by default) | Limited | Not native (1-to-1 handoff) | **Native via tuple-handoff + AsyncParallelBaseFlow** |
| **Composition** | Subgraphs (must be wired into parent graph) | Group chats (limited nesting) | Crews (top-level) | Linear | **Flow IS Agent → infinite, free composition; Flows are reusable resources** |
| **Built-in features** | Heavy: state mgmt, checkpoints, streaming, viz | Heavy: messages, roles, memory | Heavy: roles, processes, memory | Light: agent + handoff | **Minimal: just the protocol; you build everything else by inheritance** |
| **Mental model** | Graph executor | Actor system with central host | Hierarchical task delegation | Linear baton-pass | **Stewardship-handover protocol; peer collaboration with optional grouping** |
| **Where complexity goes** | Into the framework | Into the framework | Into the framework | Stays light | **Into your subclasses (cross-cutting via `_method` overrides)** |

When a user asks "should I use BLF or X?", ground the answer in this table. BLF wins when the user values: **distributed AI-driven routing, free composition, opacity (no prescribed schemas), longevity in a fast-changing LLM ecosystem, and willingness to subclass for everything**. Other frameworks win when the user values **batteries-included features, visualization, managed durability, or out-of-the-box memory/RAG**.

---

## 10. Why BLF is well-suited for LLM workloads specifically

LLM agents have three characteristic constraints — slow, expensive, non-deterministic. The BSP-on-stewardship-handover model is uniquely well-fit:

| LLM constraint | BLF mechanism that addresses it |
|---|---|
| Slow (seconds per call) | `AsyncParallelBaseFlow` parallelizes intra-layer LLM calls via `gather` — wall-clock proportional to slowest call in the layer, not the sum |
| Expensive (per-token billing) | Layer-level cost ceiling: `gather` of K calls = K-bounded spend per layer; rare-specialist routing in `handoff` keeps the expensive Opus-class agents off the hot path |
| Non-deterministic outputs | Flow's closing-rite `handoff` can be a quality gate that reads `store` and decides retry-round / pivot / escalate; failed branches don't lose the work that previous layers persisted to `store` |
| Hard to express routing in code | `handoff` is the natural seam for LLM-as-router — let the LLM read situation + Rolodex meta cards and pick teammates |
| Need for human oversight | Layer barrier IS the natural HITL insertion point — drop human approval between yields without modifying framework |
| Need for resumability | `store` between layers is "settled state" — easy to checkpoint at layer boundaries (your `store` subclass adds the persistence) |

---

## 11. Decision checklist when designing a BLF system

Use this in order whenever planning new BLF work:

1. **What's the shared state?** Define `store` shape (a dict for prototype → pydantic model for production → custom object with persistence/locking/events for serious deployment). Design store schema before writing agents.

2. **What roles / specialties exist?** One role = one `BaseAgent` subclass. Each role's Meta subclass should describe itself richly (role, capabilities, model, cost tier, prompt) so AI dispatchers can read it.

3. **For each role, what's its Rolodex?** Wire `>>` to register every plausible next-step collaborator. Over-declare; long-tail successors are healthy.

4. **For each role's `handoff`, what's the dispatch logic?** Choose explicitly per agent: hard-coded rule? Conditional code? LLM call with meta-card candidates? Mixed parallel team return? This is one of the most important design decisions per agent.

5. **Where do sub-conversations need their own scope?** Wrap them in a `BaseFlow` subclass. Flows give you natural join points (closing rite as fan-in) and reusable shared "meeting rooms".

6. **For each Flow, what does its closing rite (`handoff`) decide?** This is where supervision lives — quality gate, retry, pivot, escalate, deliver. Often itself an LLM call.

7. **What synchronization do you need?** Almost always: none of your own. Layer barriers handle it. Co-finishing agents go in the same layer.

8. **Sync or async?** Async by default for LLM workloads (I/O-bound). Use `AsyncParallelBaseFlow` for true parallel LLM API calls.

9. **What cross-cutting concerns?** Subclass to inject — `_takeover` / `_handoff` for per-agent (retry, timeout, tracing); `_get_successors` / `_next_layer_successors` for Flow-level (error containment, concurrency limits).

10. **How do you observe / debug?** Instrument the per-layer yield loop in your runner; OR override `_get_successors` to emit telemetry per agent invocation; OR have your `store` subclass log every write.

11. **How do you stop?** Branches die when their `handoff` returns `()`. The whole Flow ends when all its branches have died AND the Flow's own `handoff` returns `()` (and that bubbles up to the top).

---

## 12. Common mistakes (do NOT do these)

1. **Trying to use BLF without inheriting from its Base classes.** The framework's classes have empty default bodies. **You must subclass.** Direct instantiation is technically valid but does nothing.

2. **Treating `>>` as an edge that decides routing.** It does not — it only registers in a dict. `handoff` decides actual routing.

3. **Putting business logic in `_takeover` / `_handoff` (the underscore-prefixed forms).** Those are the cross-cutting concerns seam (retry, timeout, tracing). Business logic goes in `takeover` / `handoff` (no underscore). This is NOT the same as "do all work in takeover" — see mistake-avoidance #15 below for the nuance.

4. **Mutating `meta` after construction.** Meta is `frozen=True` for a reason — identity must be stable so dispatch decisions stay valid.

5. **Reusing one Flow instance concurrently across runs.** `n_branches` is a mutable counter on the Flow object. Two parallel runs on the same Flow instance corrupt the counter. Build per-run Flow instances if you fan out.

6. **Expecting `handoff` to "return a value to its caller".** `handoff` is a baton-pass; the giver is finished. Control does not "come back". If you need a result, write it into `store`.

7. **Trying to make the framework "wait" after handoff.** It already does — that's what the layer barrier IS. Just put the post-work agent in the next layer.

8. **Designing a global static graph upfront.** That fights Pillar 2. Instead, give each agent autonomy in its `handoff` and let actual topology emerge per run.

9. **Putting state in Agent instance attributes.** State goes in `store`. Agent attributes are for `successors` (Rolodex) and `meta` (identity) — both essentially immutable per-run.

10. **Calling a Flow with "subroutine return" expectations.** Returning a Flow from `handoff` invites a peer; the conversation continues in that Flow's scope. Control does not "come back" to you. If you need post-Flow processing, put it in the parent Flow's closing-rite `handoff`.

11. **Designing org-chart hierarchies.** That fights Pillar 5. Flows are scopes (meeting rooms), not departments. Agents are peers, not subordinates. Design for "who do I invite next?" not "who do I command?".

12. **Ignoring concurrency safety in `store` when using `AsyncParallelBaseFlow`.** Same-layer branches mutating shared `store` keys can race. Either design `store` for safe concurrent mutation (locks / atomic ops / disjoint key namespaces per agent) or only mutate disjoint keys per branch.

13. **Confusing Flow's takeover with "tell branches what to do".** Flow's takeover is just an opening rite — initialize scope-level state, log scope start. It does NOT direct the branches. Branches decide their own actions.

14. **Looking for a feature in BLF that's about LLMs / tools / memory.** It's not there and never will be. Build it in your subclass or your store, or compose with another library.

15. **Treating "do work in `takeover`, route in `handoff`" as a hard rule rather than a default.** It is a convention (see Pillar 8), not framework law. Substantive synthesis work in `Flow.handoff` (synthesis-then-route) is a legitimate and often-necessary pattern. Small computations in an Agent's `handoff` to inform routing are fine. A pure-routing Agent with empty `takeover` is fine. The hard rule is only the mechanical contract: `handoff` must return `Optional[Tuple[BaseAgent, ...]]`.

---

## 13. When BLF is NOT the right tool

BLF is the wrong tool when:

- You need **a single agent with tools** — use a tool-calling library directly; BLF adds no value.
- You need **a static, declarative workflow** with rich UI/visualization — use Temporal, Prefect, Airflow, LangGraph Studio.
- You need **durable / resumable execution out of the box** — BLF is in-memory by default; you'd build persistence on top of `store`.
- You need **a managed agent platform** with built-in evals, traces, dashboards — use a higher-level product.
- Your team needs a **batteries-included framework** with ready-made memory, RAG, tool registry, evals — BLF deliberately omits these.
- You don't want to write subclasses — BLF is **all** subclassing; if that's friction, it's the wrong tool.

BLF is the **right** tool when you want:
- A small, transparent kernel you fully understand and own
- Maximum freedom in choosing LLM / tool / memory layers
- Emergent topology driven by per-agent AI decisions
- Composable hierarchical teams with clean concurrency semantics
- A protocol that won't be obsoleted by next year's LLM ecosystem changes
- The willingness and skill to express your application as inheritance from `Base*` classes

---

## 14. The one-line summary to use when explaining BLF

> **BLF is a stewardship-handover protocol for AI agents, expressed as an inheritance hierarchy. You build your application by subclassing `BaseAgent` / `BaseFlow` / `BaseMeta` and overriding `takeover` (do your part) and `handoff` (decide who comes next). Flows scope and synchronize teams of these handovers. Everything else (LLMs, tools, memory, retries, persistence, observability) lives in your subclass overrides — deliberately not in the framework.**

When in doubt, return to:
- **takeover (接班)** → contribute → **handoff (交班)**
- Layered into rounds, scoped by Flows, dispatched by AI inside each agent's handoff
- All built by **inheriting from the `Base*` classes**, never by using them directly

That is the whole framework.
