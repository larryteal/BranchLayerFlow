"""LOCKED EVALUATOR.

Single source of truth for how a candidate report is scored. Same prompt,
same temperature, same rubric on every call -- that's what makes scores
across rounds comparable.

If you want to change *what* the loop optimizes for, edit `program.md`.
If you want to change *how* it's measured, edit this file deliberately
and start a fresh run -- you cannot mix scores from different judge
versions on the same scoreboard.

Set $JUDGE_MODEL to use a different (typically stronger) model for
judging than for proposing -- a strict TA grading a student is the
intended dynamic. Falls back to $OPENAI_MODEL.
"""

import os
from typing import Dict, List, Tuple

from utils import chat, parse_score


JUDGE_MODEL = os.environ.get("JUDGE_MODEL")  # None -> use $OPENAI_MODEL


JUDGE_SYSTEM = """\
You are an unforgiving research-report judge. Score the REPORT on TOPIC out
of 100. Use floats (one decimal). Be strict. The reference distribution:

  90+    graduate-level survey, comprehensive, every claim traceable to WEB
         FACTS, no fluff, dense with specifics
  80-89  solid undergraduate paper, all main angles covered, mostly cited,
         a few hedged claims
  70-79  competent overview, missing 1-2 important angles or many specifics
  50-69  hits major points but is generic, light on specific facts, weak
         citations, padded prose
  30-49  surface-level, mostly platitudes, almost no concrete facts
  <30    empty, badly broken, off-topic, or contradicted by WEB FACTS

HARD CAPS (apply mechanically before any rubric adjustment):
  - Report < 200 words                                                  cap 30
  - Report < 400 words                                                  cap 60
  - Report < 700 words                                                  cap 78
  - Fewer than 4 distinct concrete specifics
    (numbers, dates, named entities, version strings, URLs)             cap 55
  - Zero verbatim URLs from WEB FACTS                                   cap 65
  - Any factual claim that contradicts WEB FACTS                        cap 50
  - >= 2 occurrences of filler phrases like
    "in conclusion", "in summary", "it is important to note",
    "in today's fast-paced world", "as we move forward"                  -8

After applying the strictest cap, score within these bands:
  - Factual coverage (40)        does it span the topic comprehensively?
  - Citation quality (20)        verbatim URLs from WEB FACTS, not invented
  - Clarity & structure (20)     useful headings, paragraph flow
  - Conciseness / density (20)   every paragraph earns its place

Reply with EXACTLY two lines and nothing else:
SCORE: <number 0-100, one decimal>
BREAKDOWN: <one specific weakness the next mutation should target>
"""


async def judge(
    report: str,
    topic: str,
    web_facts: List[Dict[str, str]],
) -> Tuple[float, str]:
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
    score, breakdown = parse_score(reply)
    return score, breakdown or "(no breakdown)"
