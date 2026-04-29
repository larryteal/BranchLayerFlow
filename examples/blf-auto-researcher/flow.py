"""Multi-stage autonomous researcher with verification.

  PlanAgent           (split topic into N phases, each {title, question})
       |
       v
  ParallelPhaseFlow   (one InvestigateFlow per phase, in parallel)
       |   each per-phase flow:
       |     SearchAgent -> ExtractAgent  (extract claims, tag [weak]/[ok])
       v
  VerifyAgent         (round 1: collect [weak] claims; trigger drilldown if any)
       |
       v   if weak claims found AND first round
  ParallelDrilldownFlow  (one DrilldownAgent per weak claim, in parallel)
       |   appends verification snippets to store
       v
  VerifyAgent         (round 2: no further drilldown; -> ReportAgent)
       |
       v
  ReportAgent

Two layers of dynamic parallel fan-out — phases AND drilldowns — and a
bounded verification loop, all expressed as plain `>>` edges plus
flows-built-inside-handoffs. No external scheduler.
"""

import re
from typing import Any, Optional, Tuple

from branchlayerflow import (
    AsyncBaseAgent,
    AsyncBaseFlow,
    AsyncParallelBaseFlow,
    BaseMeta,
)

from utils import chat, parse_phases, web_search


# ----- Stage 1: plan -----

class PlanAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        n = store.get("phases", 4)
        reply = await chat([
            {
                "role": "system",
                "content": (
                    f"Split a research topic into exactly {n} phases. "
                    f"Reply with exactly {n} lines, each in the form:\n"
                    f"  PHASE: <short title> | <focused research question>"
                ),
            },
            {"role": "user", "content": store["topic"]},
        ])
        phases = parse_phases(reply)[:n]
        if not phases:
            phases = [{"title": "Overview", "question": store["topic"]}]
        store["phases_list"] = phases
        print(f"\n[plan] {len(phases)} phases:")
        for p in phases:
            print(f"  - {p['title']}: {p['question']}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        flow = build_parallel_phases(store["phases_list"])
        flow >> self.successors["verify"]
        return (flow,)


# ----- Stage 2: parallel phase investigation -----

class SearchAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        title = self.meta.title
        question = self.meta.question
        try:
            results = await web_search(question, max_results=10)
        except Exception as e:
            results = []
            print(f"[search:{title!r}] error: {e}")
        store.setdefault("phase_evidence", {})[title] = results

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["extract"],)


class ExtractAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        title = self.meta.title
        question = self.meta.question
        rows = store.get("phase_evidence", {}).get(title, [])
        if not rows:
            store.setdefault("claims", {})[title] = "[weak] (no search results)"
            return
        body = "\n".join(
            f"- {r.get('title','')}: {r.get('description','')}" for r in rows
        )
        reply = await chat([
            {
                "role": "system",
                "content": (
                    "Extract concrete factual claims as a bullet list. "
                    "Begin each line with `[ok]` if the claim is well-supported by the results, "
                    "or `[weak]` if it's speculative, missing a source, or under-evidenced. "
                    "Output 4-8 bullets, no preamble."
                ),
            },
            {"role": "user", "content": f"Phase: {title}\nQuestion: {question}\n\nResults:\n{body}"},
        ])
        store.setdefault("claims", {})[title] = reply
        print(f"\n[claims] {title}\n{reply}")


def _build_phase(p, idx: int) -> AsyncBaseFlow:
    s = SearchAgent(meta=BaseMeta(name="search", title=p["title"], question=p["question"]))
    e = ExtractAgent(meta=BaseMeta(name="extract", title=p["title"], question=p["question"]))
    s >> e
    return AsyncBaseFlow(meta=BaseMeta(name=f"phase_{idx}"), branches=(s,))


class ParallelPhaseFlow(AsyncParallelBaseFlow):
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        succ = tuple(self.successors.values())
        return succ[:1] or None


def build_parallel_phases(phases) -> ParallelPhaseFlow:
    branches = tuple(_build_phase(p, i) for i, p in enumerate(phases))
    return ParallelPhaseFlow(meta=BaseMeta(name="parallel_phases"), branches=branches)


# ----- Stage 3: verify (and optional drilldown loop) -----

def _collect_weak(store) -> list:
    weak = []
    for title, claims_text in store.get("claims", {}).items():
        for ln in claims_text.splitlines():
            if "[weak]" in ln.lower():
                claim = re.sub(r"^\s*[-*]?\s*\[weak\]\s*", "", ln, flags=re.IGNORECASE).strip()
                if claim:
                    weak.append({"phase": title, "claim": claim})
    return weak


class VerifyAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["verify_round"] = store.get("verify_round", 0) + 1
        store["weak_claims"] = _collect_weak(store)
        print(f"\n[verify] round={store['verify_round']} weak_claims={len(store['weak_claims'])}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        if not store["weak_claims"] or store["verify_round"] >= store["max_verify_rounds"]:
            return (self.successors["report"],)
        flow = build_parallel_drilldown(store["weak_claims"])
        flow >> self  # loop: drilldown bubble-up returns this VerifyAgent
        return (flow,)


class DrilldownAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        claim = self.meta.claim
        phase = self.meta.phase
        try:
            results = await web_search(claim, max_results=5)
        except Exception:
            results = []
        body = "\n".join(
            f"- {r.get('title','')}: {r.get('description','')}" for r in results
        ) or "(no follow-up results)"
        verdict = await chat([
            {
                "role": "system",
                "content": (
                    "Given a previously-weak claim and new search snippets, "
                    "output ONE line beginning with `[ok]` if now well-supported, "
                    "or `[weak]` if still under-evidenced, followed by a revised, "
                    "specific claim. No preamble."
                ),
            },
            {"role": "user", "content": f"Original claim: {claim}\n\nFollow-up results:\n{body}"},
        ])
        # Replace the matching weak line in store["claims"][phase], else append.
        old = store["claims"].get(phase, "")
        lines = old.splitlines()
        for i, ln in enumerate(lines):
            if "[weak]" in ln.lower() and claim[:60] in ln:
                lines[i] = verdict.strip()
                break
        else:
            lines.append(verdict.strip())
        store["claims"][phase] = "\n".join(lines)
        print(f"[drilldown:{phase}] {verdict.strip()}")


class ParallelDrilldownFlow(AsyncParallelBaseFlow):
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        succ = tuple(self.successors.values())
        return succ[:1] or None


def build_parallel_drilldown(weak_claims) -> ParallelDrilldownFlow:
    branches = tuple(
        DrilldownAgent(meta=BaseMeta(name=f"drill_{i}", phase=w["phase"], claim=w["claim"]))
        for i, w in enumerate(weak_claims)
    )
    return ParallelDrilldownFlow(
        meta=BaseMeta(name="parallel_drilldown"), branches=branches
    )


# ----- Stage 4: report -----

class ReportAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        body = "\n\n".join(f"## {t}\n{c}" for t, c in store.get("claims", {}).items())
        report = await chat([
            {
                "role": "system",
                "content": (
                    "Write a polished markdown research report. Use the per-phase "
                    "claims as your factual basis. Drop or hedge anything still "
                    "tagged `[weak]`. Add a short `## Caveats` section at the end "
                    "listing any remaining weak points."
                ),
            },
            {"role": "user", "content": f"Topic: {store['topic']}\n\nVerified claims:\n{body}"},
        ])
        store["report"] = report
        print(f"\n=== Final report ===\n{report}")


# ----- Wiring -----

def build_auto_researcher_flow() -> AsyncBaseFlow:
    plan = PlanAgent(meta=BaseMeta(name="plan"))
    verify = VerifyAgent(meta=BaseMeta(name="verify"))
    report = ReportAgent(meta=BaseMeta(name="report"))
    plan >> verify
    verify >> report
    return AsyncBaseFlow(meta=BaseMeta(name="auto_researcher"), branches=(plan,))
