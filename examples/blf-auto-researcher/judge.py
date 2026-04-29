"""LOCKED EVALUATOR.

Single source of truth for how a candidate report is scored. Same prompt,
same temperature, same rubric on every call -- that's what makes scores
across rounds comparable.

Per-axis scoring rather than a single global number. Each axis has explicit
criteria so the judge applies the same standard every round; the proposer
gets a structured "weakest axis + suggested next mutation" signal back.

If you want to change *what* the loop optimizes for, edit `program.md` and
this file together, then start a fresh run -- you cannot mix scores from
different judge versions on the same scoreboard.

Set $JUDGE_MODEL to use a different (typically stronger) model for judging
than for proposing -- a strict TA grading a student is the intended dynamic.
Falls back to $OPENAI_MODEL.
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

The rubric works the same for any language (English, Chinese, Japanese,
Korean, mixed). Do NOT use word count as a proxy for quality -- judge the
substance directly.

RUBRIC -- score each axis independently, then sum:

1. COVERAGE                                                       (max 20)
   Does the report address all important sub-topics implied by TOPIC?
   - 0-4    only one angle; major aspects missing
   - 5-10   most main angles touched, but several gaps
   - 11-15  all main angles covered
   - 16-20  comprehensive, including non-obvious sub-topics

2. SPECIFICITY                                                    (max 25)
   Count distinct concrete facts: numbers, dates, named entities, version
   strings, URLs, named techniques. Generic prose does NOT count.
   - 0-2 specifics                                                 -> 0-5
   - 3-5 specifics                                                 -> 6-10
   - 6-10 specifics                                                -> 11-17
   - 11-15 specifics, distributed across sections                  -> 18-22
   - 16+ specifics, well-distributed                               -> 23-25

3. SOURCING                                                       (max 15)
   Are claims traceable to verbatim URLs from WEB FACTS?
   - 0       no citations or invented URLs
   - 1-5     a few citations; most major claims uncited
   - 6-10    most major claims cited from WEB FACTS
   - 11-15   essentially every non-trivial claim cited from WEB FACTS

4. STRUCTURE                                                      (max 10)
   Useful headings, logical flow, scannable.
   - 0-2     unstructured wall of text
   - 3-6     basic sections, but order or balance is off
   - 7-10    clean structure: TL;DR + well-named sections + good balance

5. DEPTH                                                          (max 20)
   Analytical synthesis vs. listing.
   - 0-4     bullet list of disconnected facts
   - 5-10    facts grouped, minor commentary
   - 11-15   real synthesis: comparisons, tradeoffs, mechanisms explained
   - 16-20   rare: synthesis surfaces an insight not obvious from any single source

6. NOVELTY                                                        (max 10)
   Perspectives or angles a quick search would miss.
   - 0-2     pure consensus / Wikipedia summary
   - 3-6     some non-obvious framings or under-reported angles
   - 7-10    multiple non-obvious insights or critiques

HARD REJECTIONS (override rubric -> 0-15 total):
   - Empty, off-topic, or fabricated content
   - Any claim that directly contradicts WEB FACTS
   - Invented URLs (any URL not appearing verbatim in WEB FACTS)

OUTPUT FORMAT -- exactly these 9 lines, nothing else:

COVERAGE: <int>/20    -- <one short reason>
SPECIFICITY: <int>/25 -- <one short reason>
SOURCING: <int>/15    -- <one short reason>
STRUCTURE: <int>/10   -- <one short reason>
DEPTH: <int>/20       -- <one short reason>
NOVELTY: <int>/10     -- <one short reason>
SCORE: <total integer 0-100>
WEAKEST_AXIS: <COVERAGE|SPECIFICITY|SOURCING|STRUCTURE|DEPTH|NOVELTY>
NEXT: <one specific mutation that would most raise the weakest axis>
"""


_AXIS_RE = re.compile(
    r"(COVERAGE|SPECIFICITY|SOURCING|STRUCTURE|DEPTH|NOVELTY)\s*[:=]\s*(\d+)\s*/\s*(\d+)",
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
        # Compute weakest by smallest got/max ratio.
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
    """Score a report and return (score, breakdown_str, axes_dict, next_hint).

    - score:        float total 0-100
    - breakdown:    one-line summary stored on the journal
    - axes:         {axis_name: (got, max)} per-axis breakdown
    - next_hint:    judge's suggested next mutation for the weakest axis
    """
    facts_block = "\n".join(
        f"- {r.get('title','')} :: {r.get('description','')} ({r.get('url','')})"
        for r in web_facts
    ) or "(no web facts available)"
    body = (
        f"TOPIC: {topic}\n\n"
        f"WEB FACTS (only these URLs may be cited):\n{facts_block}\n\n"
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
        # Judge returned something unparseable; surface that explicitly so
        # the journal makes it visible.
        breakdown = f"(unparseable judge reply: {reply[:120]!r})"
    else:
        breakdown = (
            f"weakest={weakest}({axes.get(weakest, (0,0))[0]}/{axes.get(weakest, (0,0))[1]}) "
            f"next: {next_hint or '(no hint)'}"
        )
    return score, breakdown, axes, next_hint
