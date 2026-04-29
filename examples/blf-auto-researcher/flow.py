"""Autoresearch hill-climber on a research report.

  SeedAgent
       |  multi-angle web fetch -> rich web_facts
       |  initial draft from facts -> first scored report on the journal
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

Each candidate is judged on six axes (Coverage / Specificity / Sourcing /
Structure / Depth / Novelty). The proposer doesn't chase a vague global
score; it targets the WEAKEST_AXIS surfaced by the judge, so the loop
makes monotonic progress on the dimension that's actually limiting it.

The loop body is `select.handoff(store)` returning either a fresh beam
(continue) or the report agent (stop). No external scheduler. The keep/revert
primitive lives entirely in `SelectAgent.takeover`.
"""

import asyncio
import re
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
Output exactly 4 narrow web-search angles that DIRECTLY inform the topic
question. Each angle should be a specific search query that surfaces
evidence relevant to the question AS LITERALLY ASKED.

Do NOT drift into tangential topics. For example, for a "what is the
technical architecture / what's new" question, do NOT search for market
impact, business applications, company history, or industry trends --
those are off-topic and will be penalized later.

One angle per line, no numbering, no quotes.\
"""

DRAFT_SYSTEM = """\
Write a research report that DIRECTLY answers the topic question, using
ONLY the WEB FACTS as the source of truth.

Two non-negotiable rules (the judge will heavily penalize violations):

  1. STAY ON THE LITERAL QUESTION. Every section must directly serve the
     question. Do NOT add tangential content (market impact, company
     history, business applications, industry trends, future speculation
     unrelated to the asked-about technology) unless the question
     explicitly asks for it.

  2. NEVER FABRICATE FACTS. Every specific number, date, named entity,
     version string, technique name, or URL in your output must come
     from WEB FACTS. If WEB FACTS doesn't contain a fact, do NOT include
     it -- hedge ("according to limited information") or simply omit.
     A short, true, on-topic report scores far higher than a long one
     padded with invented specifics.

Goals (in priority order, matching the judge's axis weights):

  1. TOPIC FIDELITY (25 pts):  answer the literal question; nothing tangential
  2. FACT GROUNDING (25 pts):  every claim traceable to a WEB FACT snippet
  3. COVERAGE within scope (15 pts): hit the major on-topic sub-aspects
  4. DEPTH (15 pts):           synthesize across sources where they connect
  5. STRUCTURE (10 pts):       TL;DR + named sections + `## Caveats` at end
  6. NOVELTY (10 pts):         non-obvious framings within scope

Cite verbatim URLs from WEB FACTS in markdown link form [text](url).
Write in the same language as the topic. Do NOT pad with filler.\
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


def _format_axes(axes: dict) -> str:
    if not axes:
        return "(no axis breakdown)"
    return " | ".join(f"{k} {v[0]}/{v[1]}" for k, v in axes.items())


class SeedAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store.setdefault("report", "")
        store.setdefault("best_score", -1.0)
        store.setdefault("best_breakdown", "(initial)")
        store.setdefault("best_axes", {})
        store.setdefault("best_next_hint", "")
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

        score, breakdown, axes, next_hint = await judge(
            store["report"], store["topic"], store["web_facts"]
        )
        store["best_score"] = score
        store["best_breakdown"] = breakdown
        store["best_axes"] = axes
        store["best_next_hint"] = next_hint
        store["journal"].append({
            "round": 0,
            "slot": -1,
            "decision": "seed",
            "candidate_score": score,
            "current_best_before": -1.0,
            "mutation": "Initial draft from multi-angle web facts",
            "breakdown": breakdown,
        })
        print(f"[seed] initial draft scored {score:.1f}")
        print(f"       axes: {_format_axes(axes)}")
        print(f"       next: {next_hint}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        beam = build_beam_flow(store["beam"])
        beam >> self.successors["select"]
        return (beam,)


# ----- Beam: K parallel proposers, each is Propose -> Score -----

PROPOSE_SYSTEM = """\
You are mutating a research report to maximize a strict per-axis judge.

The two highest-weighted axes (50 of 100 points combined) are:

  TOPIC_FIDELITY (25)  -- does the report answer the LITERAL question?
                          Off-topic sections are actively penalized.
  FACT_GROUNDING (25)  -- is every specific claim supported by WEB FACTS?
                          Each unsupported claim costs 2 points; each
                          contradicted or invented one costs 5.

This means:

  - If the weakest axis is TOPIC_FIDELITY, REMOVE off-topic sections.
    Do not add more material -- trim drift, refocus the remaining text
    on the literal question.

  - If the weakest axis is FACT_GROUNDING, REMOVE unsupported claims and
    replace them with claims you can ground in WEB FACTS verbatim. If
    you cannot ground a claim, hedge it ("limited evidence suggests")
    or drop it. Do not invent numbers, dates, names, version strings,
    techniques, or URLs to look more specific.

  - For the smaller axes (Coverage, Depth, Structure, Novelty), make
    targeted additions, but every addition must be on-topic AND grounded.

Hard rules (judge will hard-reject violations):

  - Cite ONLY URLs that appear verbatim in WEB FACTS. Never invent URLs.
  - Never invent numbers, dates, names, version strings, or techniques.
    "Looks plausible" is not the standard; "appears in WEB FACTS" is.
  - Stay on the literal question. Tangential coverage is a deduction,
    not a bonus.
  - Mutations must be DIFFERENT from ones already in the journal -- the
    judge already saw those.
  - Write in the same language as TOPIC.
  - Length is NOT a quality axis. Padding will lose, not gain, points
    (FACT_GROUNDING punishes invented specifics; TOPIC_FIDELITY punishes
    off-topic padding).

Reply with EXACTLY this format and nothing else:
MUTATION: <one short sentence: VERB + WHAT, specific>
---REPORT---
<full new report markdown>
"""


def _parse_propose(reply: str) -> dict:
    mutation, _, new_report = reply.partition("---REPORT---")
    if mutation:
        mutation = mutation.replace("MUTATION:", "", 1).strip().splitlines()[0]
    else:
        mutation = "(unparseable)"
    new_report = new_report.strip() or reply.strip()
    # Strip any stray separator the LLM accidentally re-emitted at the tail.
    new_report = re.sub(r"\n*-{2,}\s*REPORT\s*-{2,}\s*$", "", new_report).strip()
    return {"mutation": mutation[:240], "report": new_report}


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
        cur_report = store["report"] or ""
        axes = store.get("best_axes", {}) or {}
        axes_line = _format_axes(axes)
        weakest = ""
        if axes:
            weakest = min(axes, key=lambda a: axes[a][0] / max(axes[a][1], 1))
        weakest_line = (
            f"WEAKEST AXIS: {weakest} ({axes[weakest][0]}/{axes[weakest][1]})"
            if weakest else "WEAKEST AXIS: (unknown)"
        )
        next_hint = store.get("best_next_hint", "")
        body = (
            f"TOPIC: {store['topic']}\n\n"
            f"CURRENT REPORT (best so far, score={store['best_score']:.1f})\n"
            f"AXES: {axes_line}\n"
            f"{weakest_line}\n"
            f"JUDGE'S SUGGESTED NEXT MUTATION: {next_hint or '(none)'}\n\n"
            f"--- CURRENT REPORT START ---\n{cur_report or '(empty)'}\n--- CURRENT REPORT END ---\n\n"
            f"RECENT JOURNAL (most recent last):\n{history}\n\n"
            f"WEB FACTS (use only these URLs for citations):\n{facts}\n\n"
            f"You are slot {slot} of {store['beam']}. Propose a mutation that raises "
            f"the WEAKEST AXIS. If your siblings are likely to also target that axis, "
            f"differentiate by attacking it from a different angle "
            f"(content vs. structure vs. citations vs. synthesis)."
        )
        reply = await chat(
            [
                {"role": "system", "content": PROPOSE_SYSTEM},
                {"role": "user", "content": body},
            ],
            temperature=0.8,
        )
        parsed = _parse_propose(reply)
        store.setdefault("candidates", {})[slot] = parsed

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["score"],)


class ScoreAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        slot = self.meta.slot
        cand = store["candidates"][slot]
        score, breakdown, axes, next_hint = await judge(
            cand["report"], store["topic"], store.get("web_facts", [])
        )
        cand["score"] = score
        cand["breakdown"] = breakdown
        cand["axes"] = axes
        cand["next_hint"] = next_hint
        print(
            f"  [r{store['round']+1} slot {slot}] score={score:5.1f}  "
            f"axes={_format_axes(axes)}  mut={cand['mutation'][:60]}"
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
            store["best_axes"] = best.get("axes", {})
            store["best_next_hint"] = best.get("next_hint", "")
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
            f"axes       = {_format_axes(store.get('best_axes', {}))}\n"
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
