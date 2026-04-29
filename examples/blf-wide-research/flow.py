"""Wide breadth-first research.

  DecomposeAgent
       |
       v
  ParallelInvestigateFlow  (N branches in parallel)
       |   each branch is its own InvestigateFlow:
       |     SearchAgent -> SummarizeAgent
       v
  AggregateAgent  (fired by the parallel flow's closing-rite handoff)

The fan-out width is decided by DecomposeAgent at runtime: it asks the LLM
to break the topic into N narrow sub-questions, then dynamically builds an
AsyncParallelBaseFlow with one branch per sub-question. Each branch is
itself a small flow (Search -> Summarize), so we get nested flows running
in parallel without any orchestration glue.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import (
    AsyncBaseAgent,
    AsyncBaseFlow,
    AsyncParallelBaseFlow,
    BaseMeta,
)

from utils import chat, split_lines, web_search


# ----- Stage 1: decompose -----

class DecomposeAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        n = store.get("breadth", 5)
        reply = await chat([
            {
                "role": "system",
                "content": (
                    f"Break a research topic into {n} narrow, distinct sub-questions "
                    f"that can be answered independently in parallel. "
                    f"Reply with exactly {n} lines, one question per line, no numbering."
                ),
            },
            {"role": "user", "content": store["topic"]},
        ])
        qs = split_lines(reply, n) or [store["topic"]]
        store["sub_questions"] = qs
        print(f"\n[decompose] {len(qs)} sub-questions:")
        for q in qs:
            print(f"  - {q}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        flow = build_parallel_investigate(store["sub_questions"])
        flow >> self.successors["aggregate"]
        return (flow,)


# ----- Stage 2: parallel investigate (each branch = Search -> Summarize) -----

class SearchAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        q = self.meta.question
        try:
            results = await web_search(q, max_results=10)
        except Exception as e:
            results = []
            print(f"[search:{q!r}] error: {e}")
        store.setdefault("evidence", {})[q] = results

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["summarize"],)


class SummarizeAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        q = self.meta.question
        rows = store.get("evidence", {}).get(q, [])
        if not rows:
            store.setdefault("notes", {})[q] = "(no results)"
            return
        body = "\n".join(
            f"- {r.get('title','')}: {r.get('description','')}" for r in rows
        )
        summary = await chat([
            {
                "role": "system",
                "content": "Summarize web search results into 3-5 short factual bullets. No fluff.",
            },
            {"role": "user", "content": f"Question: {q}\n\nResults:\n{body}"},
        ])
        store.setdefault("notes", {})[q] = summary
        print(f"\n[note] {q}\n{summary}")


def _build_one(question: str, idx: int) -> AsyncBaseFlow:
    s = SearchAgent(meta=BaseMeta(name="search", question=question))
    summ = SummarizeAgent(meta=BaseMeta(name="summarize", question=question))
    s >> summ
    return AsyncBaseFlow(meta=BaseMeta(name=f"investigate_{idx}"), branches=(s,))


class ParallelInvestigateFlow(AsyncParallelBaseFlow):
    """Fans out wired aggregate via closing-rite handoff once all branches drain."""

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        succ = tuple(self.successors.values())
        return succ[:1] or None


def build_parallel_investigate(questions) -> ParallelInvestigateFlow:
    branches = tuple(_build_one(q, i) for i, q in enumerate(questions))
    return ParallelInvestigateFlow(
        meta=BaseMeta(name="parallel_investigate"), branches=branches
    )


# ----- Stage 3: aggregate -----

class AggregateAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        notes = store.get("notes", {})
        body = "\n\n".join(f"## {q}\n{n}" for q, n in notes.items())
        report = await chat([
            {
                "role": "system",
                "content": "Write a coherent, well-structured markdown research report from per-question notes. Use headings and short paragraphs.",
            },
            {"role": "user", "content": f"Topic: {store['topic']}\n\nNotes:\n{body}"},
        ])
        store["report"] = report
        print(f"\n=== Final report ===\n{report}")


# ----- Wiring -----

def build_wide_research_flow() -> AsyncBaseFlow:
    decompose = DecomposeAgent(meta=BaseMeta(name="decompose"))
    aggregate = AggregateAgent(meta=BaseMeta(name="aggregate"))
    decompose >> aggregate  # name lookup target for handoff
    return AsyncBaseFlow(meta=BaseMeta(name="wide_research"), branches=(decompose,))
