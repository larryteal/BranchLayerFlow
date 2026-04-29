"""Iterative deepening research with gap-driven follow-ups.

  PlannerAgent           (write N queries from topic + known gaps)
       |
       v
  ParallelSearchFlow     (N web searches in parallel; closing-rite -> analyze)
       |
       v
  AnalyzeAgent           (SUFFICIENT? -> report; else GAP lines -> loop to plan)
       |--> ReportAgent
       \\--> PlannerAgent (next round)

Each round dynamically rebuilds the parallel search sub-flow with fresh
queries — the breadth is fixed but the queries change as the picture sharpens.
The whole machine is a loop of (plan -> parallel search -> analyze) that
exits to ReportAgent when the analyzer says it has enough or budget is spent.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import (
    AsyncBaseAgent,
    AsyncBaseFlow,
    AsyncParallelBaseFlow,
    BaseMeta,
)

from utils import chat, split_lines, web_search


# ----- Plan -----

class PlannerAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["round"] = store.get("round", 0) + 1
        gaps = store.get("gaps", [])
        gap_block = "\n".join(f"- {g}" for g in gaps) if gaps else "(initial round)"
        n = store["breadth"]
        reply = await chat([
            {
                "role": "system",
                "content": (
                    f"Write {n} short, focused web search queries. "
                    f"Reply with exactly {n} lines, one query per line, no numbering."
                ),
            },
            {"role": "user", "content": f"Topic: {store['topic']}\n\nKnown gaps:\n{gap_block}"},
        ])
        store["pending_queries"] = split_lines(reply, n) or [store["topic"]]
        print(f"\n[round {store['round']}] queries: {store['pending_queries']}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        flow = build_parallel_search(store["pending_queries"])
        flow >> self.successors["analyze"]
        return (flow,)


# ----- Parallel search -----

class SearchAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        q = self.meta.query
        try:
            results = await web_search(q, max_results=10)
        except Exception as e:
            results = []
            print(f"[search:{q!r}] error: {e}")
        store.setdefault("evidence", []).append(
            {"round": store["round"], "q": q, "results": results}
        )


class ParallelSearchFlow(AsyncParallelBaseFlow):
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        succ = tuple(self.successors.values())
        return succ[:1] or None


def build_parallel_search(queries) -> ParallelSearchFlow:
    branches = tuple(
        SearchAgent(meta=BaseMeta(name=f"search_{i}", query=q))
        for i, q in enumerate(queries)
    )
    return ParallelSearchFlow(meta=BaseMeta(name="parallel_search"), branches=branches)


# ----- Analyze (loop or exit) -----

def _evidence_block(store) -> str:
    lines = []
    for e in store.get("evidence", []):
        lines.append(f"\n[r{e['round']}] Q: {e['q']}")
        for r in e["results"]:
            lines.append(f"  - {r.get('title','')}: {r.get('description','')}")
    return "\n".join(lines) or "(no evidence)"


class AnalyzeAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        reply = await chat([
            {
                "role": "system",
                "content": (
                    "Analyze the gathered evidence. Reply with EXACTLY one of:\n"
                    "  - the literal token `SUFFICIENT` if findings cover the topic well, OR\n"
                    "  - one or more lines of the form `GAP: <missing piece>`."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {store['topic']}\n"
                    f"Round: {store['round']} / {store['max_rounds']}\n\n"
                    f"Evidence:{_evidence_block(store)}"
                ),
            },
        ])
        if "SUFFICIENT" in reply.upper() or store["round"] >= store["max_rounds"]:
            store["gaps"] = []
            store["done"] = True
        else:
            store["gaps"] = [
                ln.partition("GAP:")[2].strip()
                for ln in reply.splitlines()
                if "GAP:" in ln.upper()
            ][: store["breadth"]]
        print(f"\n[analyze] round={store['round']} done={store.get('done')} gaps={store.get('gaps')}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        if store.get("done"):
            return (self.successors["report"],)
        return (self.successors["plan"],)


class ReportAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        report = await chat([
            {
                "role": "system",
                "content": "Write a tight markdown research report. Use headings and short paragraphs.",
            },
            {
                "role": "user",
                "content": f"Topic: {store['topic']}\n\nEvidence:{_evidence_block(store)}",
            },
        ])
        store["report"] = report
        print(f"\n=== Final report ===\n{report}")


def build_deep_research_flow() -> AsyncBaseFlow:
    plan = PlannerAgent(meta=BaseMeta(name="plan"))
    analyze = AnalyzeAgent(meta=BaseMeta(name="analyze"))
    report = ReportAgent(meta=BaseMeta(name="report"))
    plan >> analyze
    analyze >> plan    # loop
    analyze >> report  # exit
    return AsyncBaseFlow(meta=BaseMeta(name="deep_research"), branches=(plan,))
