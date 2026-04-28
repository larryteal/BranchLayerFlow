"""Recursive deep research.

  PlannerAgent       (3 search queries)
        |
        v
  research sub-flow  (3 SearchAgents in parallel + extractor in next layer)
        |
        v
  SynthesiseAgent    (sufficient? if not and round < max, loop back to planner)
"""

import asyncio
from typing import Any, Optional, Tuple

from branchlayerflow import (
    AsyncBaseAgent, AsyncBaseFlow, AsyncParallelBaseFlow, BaseMeta,
)

from utils import chat, fake_search, split_lines


# ----- Planner -----

class PlannerAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        gaps = "\n".join(f"- {g}" for g in store.get("gaps", [])) or "(none yet)"
        reply = await chat([
            {"role": "system", "content": "You write 3 diverse, focused web search queries."},
            {"role": "user", "content": (
                f"Topic: {store['topic']}\n\nKnown gaps to address:\n{gaps}\n\n"
                "Reply with exactly 3 short search queries, one per line."
            )},
        ])
        store["pending_queries"] = split_lines(reply, 3) or [store["topic"]]
        print(f"\n[round {store.get('round', 0)+1}] queries: {store['pending_queries']}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["research"],)


# ----- Research sub-flow -----

class SearchAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        snippets = await fake_search(self.meta.query)
        store.setdefault("raw_snippets", []).append({"q": self.meta.query, "snippets": snippets})


class ExtractAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        last_round = store["raw_snippets"][-3:]
        body = "\n\n".join(
            f"Q: {x['q']}\n" + "\n".join(f"- {s}" for s in x["snippets"])
            for x in last_round
        )
        facts = await chat([
            {"role": "system", "content": "Extract key facts as bullet points."},
            {"role": "user", "content": f"Topic: {store['topic']}\n\nSearch results:\n{body}"},
        ])
        store.setdefault("facts", []).extend(split_lines(facts, 12))


class ResearchFlow(AsyncParallelBaseFlow):
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["extract"],)


def _build_research_subflow(queries) -> ResearchFlow:
    branches = tuple(
        SearchAgent(meta=BaseMeta(name=f"search_{i}", query=q))
        for i, q in enumerate(queries)
    )
    extract = ExtractAgent(meta=BaseMeta(name="extract"))
    flow = ResearchFlow(meta=BaseMeta(name="research"), branches=branches)
    flow >> extract
    return flow


# ----- Outer planner -> synthesise loop -----

class _PlannerWrapper(AsyncBaseAgent):
    """Builds (or rebuilds) the research sub-flow each round."""

    async def takeover(self, store: Any) -> None:
        await PlannerAgent(meta=BaseMeta(name="_inline_planner")).takeover(store)
        store["round"] = store.get("round", 0) + 1

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (_build_research_subflow(store["pending_queries"]), self.successors["synth"])


class SynthesiseAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        facts_block = "\n".join(f"- {f}" for f in store["facts"])
        reply = await chat([
            {"role": "system", "content": (
                "You decide whether the gathered facts suffice for a thorough report. "
                "If sufficient, reply EXACTLY `SUFFICIENT`. Otherwise reply with "
                "lines of the form `GAP: <missing piece>`."
            )},
            {"role": "user", "content": f"Topic: {store['topic']}\n\nFacts so far:\n{facts_block}"},
        ])
        if "SUFFICIENT" in reply.upper() or store["round"] >= store["max_rounds"]:
            store["report"] = await chat([
                {"role": "system", "content": "Write a concise markdown research report."},
                {"role": "user", "content": f"Topic: {store['topic']}\n\nFacts:\n{facts_block}"},
            ])
            store["done"] = True
            print(f"\n=== Final report ===\n{store['report']}")
        else:
            store["gaps"] = [line.partition("GAP:")[2].strip() for line in reply.splitlines() if "GAP:" in line]
            print(f"\nGaps -> {store['gaps']}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        if store.get("done"):
            return ()
        return (self.successors["plan"],)


def build_deep_research_flow() -> AsyncBaseFlow:
    plan = _PlannerWrapper(meta=BaseMeta(name="plan"))
    synth = SynthesiseAgent(meta=BaseMeta(name="synth"))
    plan >> synth
    synth >> plan
    return AsyncBaseFlow(meta=BaseMeta(name="deep_research"), branches=(plan,))
