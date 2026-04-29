"""LOCKED EVALUATOR.

Single source of truth for how a candidate report is scored. Same prompt,
same temperature, same rubric on every call -- that's what makes scores
across rounds comparable.

The two highest-weighted axes are TOPIC_FIDELITY (does it answer the
literal question?) and FACT_GROUNDING (is every claim supported by WEB
FACTS?). This is deliberate: a faithful, narrow, well-grounded report
beats a long, broad, fact-padded one. A pure-counting rubric would
incentivize hallucinated specifics and tangential coverage; this rubric
penalizes both.

If you want to change *what* the loop optimizes for, edit `program.md`
and this file together, then start a fresh run -- you cannot mix scores
from different judge versions on the same scoreboard.

Set $JUDGE_MODEL to use a different (typically stronger) model for
judging than for proposing -- a strict TA grading a student is the
intended dynamic. Falls back to $OPENAI_MODEL.

Note on limits: WEB FACTS are search-result snippets (titles +
descriptions), not full page content, so the judge can only ground
claims against snippets. A fact mentioned in the snippet is verifiable;
a fact that would need the full page is not. Use a stronger judge model
to push the ceiling on FACT_GROUNDING.
"""

import os
import re
from typing import Dict, List, Tuple

from utils import chat


JUDGE_MODEL = os.environ.get("JUDGE_MODEL")  # None -> use $OPENAI_MODEL


JUDGE_SYSTEM = """\
You are a strict, fair research-report judge. Score the REPORT on TOPIC against
the WEB FACTS using the rubric below. Be discriminating: the median report
should land in the 60s; only graduate-survey-quality work earns 90+.

Critical: the report is only valuable if (a) it answers the SPECIFIC question
in TOPIC, and (b) every claim is supported by WEB FACTS. Length, breadth,
structural polish, or fact-counting do NOT compensate for off-topic drift
or unsupported / fabricated claims. Your job is to enforce both bars.

The rubric works the same in any language (English, Chinese, mixed).

RUBRIC -- score each axis independently, then sum:

1. TOPIC_FIDELITY                                                 (max 25)
   Does the report answer the SPECIFIC question in TOPIC, without drifting
   into tangential or merely-related material?
   - 0-5    largely off-topic, generic, or answers a different question
   - 6-12   partially on-topic; multiple sections drift to tangential material
   - 13-18  mostly on-topic; small amount of drift
   - 19-22  on-topic throughout; every section directly serves the question
   - 23-25  laser-focused; nothing extraneous
   Mechanical rule: deduct ~3 points per section that does NOT directly
   answer the literal question. Examples of off-topic content for a
   "what is the architecture / what's new" question: market impact,
   business applications, company history, industry trends, future
   speculation unrelated to the stated technology, generic comparisons
   to unrelated competitors. If the topic asks for "X", a section about
   "applications of X in education" is off-topic unless the topic
   explicitly asks for applications.

2. FACT_GROUNDING                                                 (max 25)
   For each substantive claim in the REPORT (a specific number, date,
   named entity, version string, technique name, statistic, URL), find
   whether it is supported by WEB FACTS:
   - Claim is supported by a WEB FACT (snippet text or URL)         no penalty
   - Claim is NOT supported by any WEB FACT                         -2 each
   - Claim CONTRADICTS a WEB FACT                                   -5 each
   - URL cited that does NOT appear verbatim in WEB FACTS           -5 each
   Floor at 0. Reports with majority-fabricated specifics score under 8.
   This is the anti-hallucination axis. Do not give the benefit of the
   doubt: if you cannot find supporting text in WEB FACTS, the claim
   is unsupported.

3. COVERAGE (within scope)                                        (max 15)
   Within the on-topic scope, does the report cover the major sub-aspects
   the question implies? Tangential coverage does NOT count here either --
   if the topic asks about technical architecture, "covering" market
   impact does not raise this score.
   - 0-3    only one aspect addressed
   - 4-8    several aspects, with gaps
   - 9-12   all main on-topic aspects covered
   - 13-15  comprehensive within scope; non-obvious on-topic aspects included

4. DEPTH                                                          (max 15)
   Real synthesis vs. listing.
   - 0-3    bullet list of disconnected facts
   - 4-8    facts grouped, minor commentary
   - 9-12   real synthesis: comparisons, tradeoffs, mechanisms explained
   - 13-15  rare: synthesis surfaces an insight not obvious from any single source

5. STRUCTURE                                                      (max 10)
   Useful headings, logical flow, scannable.
   - 0-2    unstructured wall of text
   - 3-6    basic sections, but order or balance is off
   - 7-10   clean structure: TL;DR + well-named sections + good balance

6. NOVELTY                                                        (max 10)
   Non-obvious framings WITHIN the on-topic scope.
   - 0-2    pure consensus / Wikipedia-style summary
   - 3-6    some non-obvious on-topic framings or under-reported angles
   - 7-10   multiple non-obvious on-topic insights or critiques

HARD REJECTIONS (override rubric -> 0-15 total):
   - Empty report
   - Off-topic to the point of answering a DIFFERENT question
   - Majority-fabricated content (more than half of specifics not in WEB FACTS)
   - Any URL cited that does not appear verbatim in WEB FACTS

OUTPUT FORMAT -- exactly these 9 lines, nothing else:

TOPIC_FIDELITY: <int>/25 -- <one short reason; name any drifting sections>
FACT_GROUNDING: <int>/25 -- <count and list the worst unsupported / contradicted claims>
COVERAGE: <int>/15       -- <one short reason>
DEPTH: <int>/15          -- <one short reason>
STRUCTURE: <int>/10      -- <one short reason>
NOVELTY: <int>/10        -- <one short reason>
SCORE: <total integer 0-100>
WEAKEST_AXIS: <TOPIC_FIDELITY|FACT_GROUNDING|COVERAGE|DEPTH|STRUCTURE|NOVELTY>
NEXT: <one specific mutation that would most raise the weakest axis>
"""


_AXIS_RE = re.compile(
    r"(TOPIC_FIDELITY|FACT_GROUNDING|COVERAGE|DEPTH|STRUCTURE|NOVELTY)\s*[:=]\s*(\d+)\s*/\s*(\d+)",
    re.IGNORECASE,
)
_TOTAL_RE = re.compile(r"SCORE\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
_WEAK_RE = re.compile(r"WEAKEST_AXIS\s*[:=]\s*([A-Za-z_]+)", re.IGNORECASE)
_NEXT_RE = re.compile(r"NEXT\s*[:=]\s*(.+)", re.IGNORECASE)


def _parse_judge(reply: str):
    axes: Dict[str, Tuple[int, int]] = {}
    for m in _AXIS_RE.finditer(reply):
        axes[m.group(1).upper()] = (int(m.group(2)), int(m.group(3)))
    total = -1.0
    tm = _TOTAL_RE.search(reply)
    if tm:
        try:
            total = float(tm.group(1))
        except ValueError:
            pass
    if total < 0 and axes:
        total = float(sum(got for got, _ in axes.values()))
    weakest = ""
    wm = _WEAK_RE.search(reply)
    if wm:
        weakest = wm.group(1).strip().upper()
    if not weakest and axes:
        weakest = min(axes, key=lambda a: axes[a][0] / max(axes[a][1], 1))
    next_mut = ""
    nm = _NEXT_RE.search(reply)
    if nm:
        next_mut = nm.group(1).strip().splitlines()[0][:240]
    return total, axes, weakest, next_mut


async def judge(
    report: str,
    topic: str,
    web_facts: List[Dict[str, str]],
):
    """Score a report and return (score, breakdown_str, axes_dict, next_hint)."""
    facts_block = "\n".join(
        f"- {r.get('title','')} :: {r.get('description','')} ({r.get('url','')})"
        for r in web_facts
    ) or "(no web facts available)"
    body = (
        f"TOPIC: {topic}\n\n"
        f"WEB FACTS (only these URLs may be cited; only their snippet text "
        f"may ground a claim):\n{facts_block}\n\n"
        f"REPORT:\n{report or '(empty)'}\n"
    )
    reply = await chat(
        [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": body},
        ],
        model=JUDGE_MODEL,
        temperature=0.0,
    )
    score, axes, weakest, next_hint = _parse_judge(reply)
    if not axes:
        breakdown = f"(unparseable judge reply: {reply[:120]!r})"
    else:
        breakdown = (
            f"weakest={weakest}({axes.get(weakest, (0,0))[0]}/{axes.get(weakest, (0,0))[1]}) "
            f"next: {next_hint or '(no hint)'}"
        )
    return score, breakdown, axes, next_hint
