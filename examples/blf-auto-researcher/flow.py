"""Autoresearch hill-climber on a research report.

  SeedAgent
       |  fetch one-shot web facts; init journal, best=-1
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


# ----- Seed: one-shot fact fetch + state init -----

class SeedAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store.setdefault("report", "")
        store.setdefault("best_score", -1.0)
        store.setdefault("best_breakdown", "(initial)")
        store.setdefault("round", 0)
        store.setdefault("streak_no_improvement", 0)
        store.setdefault("journal", [])
        store["candidates"] = {}
        try:
            store["web_facts"] = await web_search(store["topic"], max_results=10)
        except Exception as e:
            print(f"[seed] web_search failed: {e}")
            store["web_facts"] = []
        print(
            f"\n[seed] topic={store['topic']!r}\n"
            f"       budget={store['budget']} beam={store['beam']} "
            f"target={store['target_score']} patience={store['patience']}\n"
            f"       fetched {len(store['web_facts'])} web facts"
        )

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        beam = build_beam_flow(store["beam"])
        beam >> self.successors["select"]
        return (beam,)


# ----- Beam: K parallel proposers, each is Propose -> Score -----

PROPOSE_SYSTEM = """\
You are mutating a research report to maximize its judge score.

Pick ONE small, motivated mutation. Smaller diffs are better -- a 1-point
gain from removing fluff beats a 1-point gain that adds a section. Cite
sources only from the WEB FACTS provided. Do not invent URLs.

Reply with EXACTLY this format and nothing else:
MUTATION: <one short sentence describing the change>
---REPORT---
<the full new report markdown>
"""


class ProposeAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        slot = self.meta.slot
        history_lines = []
        for j in store["journal"][-8:]:
            history_lines.append(
                f"  r{j['round']} {j['decision']:<6} score={j['candidate_score']:>5.1f} "
                f":: {j['mutation'][:80]}"
            )
        history = "\n".join(history_lines) or "  (no prior rounds)"
        facts = "\n".join(
            f"- {r.get('title','')} :: {r.get('description','')[:160]}"
            for r in store.get("web_facts", [])
        ) or "(no facts)"
        body = (
            f"TOPIC: {store['topic']}\n\n"
            f"CURRENT REPORT (best so far, score={store['best_score']:.1f}, "
            f"breakdown: {store['best_breakdown']}):\n"
            f"{store['report'] or '(empty)'}\n\n"
            f"RECENT JOURNAL (most recent last):\n{history}\n\n"
            f"WEB FACTS (use only these for citations):\n{facts}\n\n"
            f"You are slot {slot}. Make your mutation distinct from siblings if you can."
        )
        reply = await chat(
            [
                {"role": "system", "content": PROPOSE_SYSTEM},
                {"role": "user", "content": body},
            ],
            temperature=0.7,
        )
        mutation, _, new_report = reply.partition("---REPORT---")
        mutation = mutation.replace("MUTATION:", "", 1).strip().splitlines()[0] if mutation else "(unparseable)"
        new_report = new_report.strip()
        if not new_report:
            # Couldn't parse; fall back to the whole reply as the report.
            new_report = reply.strip()
        store.setdefault("candidates", {})[slot] = {
            "mutation": mutation[:200],
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
            f"mut={cand['mutation'][:70]}"
        )


class ParallelBeamFlow(AsyncParallelBaseFlow):
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        succ = tuple(self.successors.values())
        return succ[:1] or None


def _build_slot(slot_idx: int) -> AsyncBaseFlow:
    # Names inside a slot don't need to be globally unique; per-instance
    # successors dict keys on meta.name. Keep them short so the handoff
    # lookups (`self.successors["score"]`) work uniformly across slots.
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
