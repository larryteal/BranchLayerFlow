"""Autoresearch hill-climber on a research report.

  SeedAgent
       |  multi-angle web fetch -> rich web_facts
       |  initial draft from facts -> first scored report
       v
  ParallelBeamFlow         (K proposers in parallel, K = beam)
       |   each branch is a slot sub-flow:
       |     ProposeAgent -> ScoreAgent
       v
  SelectAgent              (pick best candidate; keep iff score > best;
       |                     append to journal; check stop conditions)
       v
       +--- if continue --> ParallelBeamFlow (next round)  -- loops back to SelectAgent
       |
       v   else (target / budget / patience hit)
  ReportAgent              (dump output/report.md + output/journal.tsv)

The loop body is `select.handoff(store)` returning either a fresh beam
(continue) or the report agent (stop). No external scheduler. The keep/revert
primitive lives entirely in `SelectAgent.takeover`.
"""

import asyncio
from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import (
    AsyncBaseAgent,
    AsyncBaseFlow,
    AsyncParallelBaseFlow,
    BaseMeta,
)

from judge import judge
from utils import chat, web_search


# ----- Seed: multi-angle facts + initial draft + initial score -----

ANGLE_PROMPT = """\
Output exactly 4 narrow web-search angles for the topic. Each angle should
target a distinct facet (background, current state, evidence/specifics,
edge cases / criticisms). One angle per line, no numbering, no quotes.\
"""

DRAFT_SYSTEM = """\
Write a comprehensive, well-cited research report on the topic using the
WEB FACTS as the source of truth. Hard requirements:

  - Aim for 700-1200 words
  - Use 4-6 H2 sections plus a one-paragraph TL;DR up top
  - Pack each paragraph with specific facts: numbers, dates, version
    strings, named entities, URLs from WEB FACTS
  - Cite verbatim URLs from WEB FACTS in markdown link form [text](url)
  - End with a short `## Caveats` section listing what is unknown or contested
  - No filler ("in conclusion", "in today's world", etc.)

Do NOT invent URLs. If a claim has no source in WEB FACTS, either drop it
or hedge it explicitly.\
"""


async def _collect_facts(topic: str) -> list:
    """Fan out to 4 angle-searches in parallel, dedupe by URL."""
    try:
        angles_reply = await chat(
            [
                {"role": "system", "content": ANGLE_PROMPT},
                {"role": "user", "content": topic},
            ],
            temperature=0.3,
        )
    except Exception as e:
        print(f"[seed] angle planning failed: {e}; falling back to topic-only")
        angles_reply = topic
    angles = [
        ln.strip(" -*\"'\t")
        for ln in angles_reply.splitlines()
        if ln.strip()
    ][:4] or [topic]

    async def _safe(q):
        try:
            return await web_search(q, max_results=10)
        except Exception as e:
            print(f"[seed] web_search({q!r}) failed: {e}")
            return []

    bundles = await asyncio.gather(*[_safe(a) for a in angles])
    seen = set()
    facts = []
    for bundle in bundles:
        for r in bundle:
            url = r.get("url")
            if url and url not in seen:
                seen.add(url)
                facts.append(r)
    return facts


class SeedAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store.setdefault("report", "")
        store.setdefault("best_score", -1.0)
        store.setdefault("best_breakdown", "(initial)")
        store.setdefault("round", 0)
        store.setdefault("streak_no_improvement", 0)
        store.setdefault("journal", [])
        store["candidates"] = {}

        store["web_facts"] = await _collect_facts(store["topic"])
        print(
            f"\n[seed] topic={store['topic']!r}\n"
            f"       budget={store['budget']} beam={store['beam']} "
            f"target={store['target_score']} patience={store['patience']}\n"
            f"       gathered {len(store['web_facts'])} unique facts across angles"
        )

        facts_block = "\n".join(
            f"- {r.get('title','')} :: {r.get('description','')} ({r.get('url','')})"
            for r in store["web_facts"]
        ) or "(no facts)"
        draft = await chat(
            [
                {"role": "system", "content": DRAFT_SYSTEM},
                {"role": "user", "content": f"TOPIC: {store['topic']}\n\nWEB FACTS:\n{facts_block}"},
            ],
            temperature=0.4,
        )
        store["report"] = (draft or "").strip()

        score, breakdown = await judge(store["report"], store["topic"], store["web_facts"])
        store["best_score"] = score
        store["best_breakdown"] = breakdown
        store["journal"].append({
            "round": 0,
            "slot": -1,
            "decision": "seed",
            "candidate_score": score,
            "current_best_before": -1.0,
            "mutation": "Initial draft from multi-angle web facts",
            "breakdown": breakdown,
        })
        print(f"[seed] initial draft scored {score:.1f}: {breakdown}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        beam = build_beam_flow(store["beam"])
        beam >> self.successors["select"]
        return (beam,)


# ----- Beam: K parallel proposers, each is Propose -> Score -----

PROPOSE_SYSTEM = """\
You are mutating a research report to maximize a strict judge's score.
The judge rewards SPECIFICS, depth, and verbatim citations from WEB FACTS.
It penalizes generic prose, platitudes, and short / thin reports
(reports under 700 words are hard-capped at 78).

Pick ONE substantial mutation. Each mutation MUST do at least one of:
  - Add >= 150 words of new substantive content (numbers, dates, named
    entities, version strings, URLs)
  - Replace a section of generic prose with concrete, cited claims
  - Add a missing major angle the topic obviously requires
  - Restructure for genuine improvement (not cosmetic reordering)
  - Aggressively cut fluff -- deletion is a valid mutation if it raises
    specificity density without dropping below the word-count caps

DO NOT propose:
  - "Add a citation" without naming what gets cited
  - "Add an introduction" without saying what it contains
  - Cosmetic reformatting
  - Mutations similar to ones already KEPT (already in current report)
  - Mutations similar to ones already REVERTED (already failed)

Cite ONLY URLs that appear verbatim in WEB FACTS. Never invent URLs.

Reply with EXACTLY this format and nothing else:
MUTATION: <one short sentence: VERB + WHAT, specific>
---REPORT---
<full new report markdown, with substantive changes vs current>
"""


def _next_cap_target(words: int) -> str:
    """Tell the proposer which judge word-count cap is currently binding."""
    if words < 200:
        return "current report is below 200 words; judge caps at 30. Push above 200 immediately."
    if words < 400:
        return f"current report is {words} words; judge caps at 60 below 400. Push above 400."
    if words < 700:
        return f"current report is {words} words; judge caps at 78 below 700. Push above 700."
    if words < 1100:
        return f"current report is {words} words; no cap binding, but more depth/specifics still help."
    return f"current report is {words} words; long enough -- focus on density, not length."


class ProposeAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        slot = self.meta.slot
        history_lines = []
        for j in store["journal"][-10:]:
            history_lines.append(
                f"  r{j['round']} {j['decision']:<6} score={j['candidate_score']:>5.1f} "
                f":: {j['mutation'][:90]}"
            )
        history = "\n".join(history_lines) or "  (no prior rounds)"
        facts = "\n".join(
            f"- {r.get('title','')} :: {r.get('description','')[:200]} ({r.get('url','')})"
            for r in store.get("web_facts", [])
        ) or "(no facts)"
        words = len((store["report"] or "").split())
        body = (
            f"TOPIC: {store['topic']}\n\n"
            f"CURRENT REPORT (best so far, score={store['best_score']:.1f}, "
            f"{words} words; judge breakdown: {store['best_breakdown']})\n"
            f"BINDING CONSTRAINT: {_next_cap_target(words)}\n\n"
            f"{store['report'] or '(empty)'}\n\n"
            f"RECENT JOURNAL (most recent last):\n{history}\n\n"
            f"WEB FACTS (use only these for citations):\n{facts}\n\n"
            f"You are slot {slot} of {store['beam']}. Make your mutation distinct "
            f"from sibling slots and from prior journal entries -- explore a "
            f"different axis (depth, breadth, structure, density). If a word-count "
            f"cap is binding, the only mutation that will move the score is one "
            f"that pushes past that cap with substantive new content."
        )
        reply = await chat(
            [
                {"role": "system", "content": PROPOSE_SYSTEM},
                {"role": "user", "content": body},
            ],
            temperature=0.8,
        )
        mutation, _, new_report = reply.partition("---REPORT---")
        if mutation:
            mutation = mutation.replace("MUTATION:", "", 1).strip().splitlines()[0]
        else:
            mutation = "(unparseable)"
        new_report = new_report.strip()
        if not new_report:
            new_report = reply.strip()
        store.setdefault("candidates", {})[slot] = {
            "mutation": mutation[:240],
            "report": new_report,
        }

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["score"],)


class ScoreAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        slot = self.meta.slot
        cand = store["candidates"][slot]
        score, breakdown = await judge(
            cand["report"], store["topic"], store.get("web_facts", [])
        )
        cand["score"] = score
        cand["breakdown"] = breakdown
        print(
            f"  [r{store['round']+1} slot {slot}] score={score:5.1f}  "
            f"mut={cand['mutation'][:80]}"
        )


class ParallelBeamFlow(AsyncParallelBaseFlow):
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        succ = tuple(self.successors.values())
        return succ[:1] or None


def _build_slot(slot_idx: int) -> AsyncBaseFlow:
    propose = ProposeAgent(meta=BaseMeta(name="propose", slot=slot_idx))
    score = ScoreAgent(meta=BaseMeta(name="score", slot=slot_idx))
    propose >> score
    return AsyncBaseFlow(meta=BaseMeta(name=f"slot_{slot_idx}"), branches=(propose,))


def build_beam_flow(beam: int) -> ParallelBeamFlow:
    branches = tuple(_build_slot(i) for i in range(beam))
    return ParallelBeamFlow(meta=BaseMeta(name="beam"), branches=branches)


# ----- Select: keep/revert + journal + loop control -----

class SelectAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["round"] += 1
        cands = store.get("candidates", {})
        if not cands:
            store["last_decision"] = "revert"
            return
        best_slot = max(cands, key=lambda s: cands[s]["score"])
        best = cands[best_slot]
        keep = best["score"] > store["best_score"]
        store["journal"].append({
            "round": store["round"],
            "slot": best_slot,
            "decision": "keep" if keep else "revert",
            "candidate_score": best["score"],
            "current_best_before": store["best_score"],
            "mutation": best["mutation"],
            "breakdown": best["breakdown"],
        })
        if keep:
            store["report"] = best["report"]
            store["best_score"] = best["score"]
            store["best_breakdown"] = best["breakdown"]
            store["streak_no_improvement"] = 0
            store["last_decision"] = "keep"
            print(
                f"[r{store['round']} KEEP ] best -> {best['score']:.1f}  "
                f"({best['mutation'][:80]})"
            )
        else:
            store["streak_no_improvement"] += 1
            store["last_decision"] = "revert"
            print(
                f"[r{store['round']} REVERT] best={store['best_score']:.1f} "
                f"cand={best['score']:.1f} streak={store['streak_no_improvement']}"
            )
        store["candidates"] = {}

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        if store["best_score"] >= store["target_score"]:
            print(f"[stop] target_score {store['target_score']} reached")
            return (self.successors["report"],)
        if store["round"] >= store["budget"]:
            print(f"[stop] budget {store['budget']} exhausted")
            return (self.successors["report"],)
        if store["streak_no_improvement"] >= store["patience"]:
            print(f"[stop] {store['patience']} rounds without improvement")
            return (self.successors["report"],)
        beam = build_beam_flow(store["beam"])
        beam >> self
        return (beam,)


# ----- Report: dump artifact + journal -----

class ReportAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        out_dir = Path(store.get("out_dir", "output"))
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "report.md"
        journal_path = out_dir / "journal.tsv"
        report_path.write_text(store["report"] or "(no report produced)")
        with journal_path.open("w") as f:
            f.write("round\tslot\tdecision\tcandidate_score\tcurrent_best_before\tmutation\tbreakdown\n")
            for j in store["journal"]:
                row = [
                    str(j["round"]),
                    str(j["slot"]),
                    j["decision"],
                    f"{j['candidate_score']:.1f}",
                    f"{j['current_best_before']:.1f}",
                    j["mutation"].replace("\t", " ")[:200],
                    j["breakdown"].replace("\t", " ")[:200],
                ]
                f.write("\t".join(row) + "\n")
        print(
            f"\n=== Done ===\n"
            f"best_score = {store['best_score']:.1f}\n"
            f"rounds run = {store['round']}\n"
            f"report     -> {report_path}\n"
            f"journal    -> {journal_path}"
        )


# ----- Wiring -----

def build_autoresearch_flow() -> AsyncBaseFlow:
    seed = SeedAgent(meta=BaseMeta(name="seed"))
    select = SelectAgent(meta=BaseMeta(name="select"))
    report = ReportAgent(meta=BaseMeta(name="report"))
    seed >> select   # name lookup target inside SeedAgent.handoff
    select >> report  # name lookup target for stop transitions
    return AsyncBaseFlow(meta=BaseMeta(name="autoresearch"), branches=(seed,))
