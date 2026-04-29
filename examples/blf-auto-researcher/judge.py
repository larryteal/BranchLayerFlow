"""LOCKED EVALUATOR.

This module is the single source of truth for how a candidate report is
scored. It is the autoresearch equivalent of a fixed eval harness: do not
modify it from inside the loop. Same prompt, same temperature, same rubric
on every call -- that's what makes scores across rounds comparable.

If you want to change *what* the loop optimizes for, edit `program.md`
(the human's control file). If you want to change *how* it's measured,
edit this file deliberately and start a fresh run -- you cannot mix
scores from different judge versions on the same scoreboard.
"""

from typing import Dict, List, Tuple

from utils import chat, parse_score


JUDGE_SYSTEM = """\
You are a strict research-report judge. Score the REPORT on TOPIC out of 100.

Rubric (sum to 100):
- Factual coverage of the topic                                       (40 pts)
- Citation quality / verifiability against the provided WEB FACTS     (20 pts)
- Clarity and structure (headings, paragraph flow, no rambling)        (20 pts)
- Conciseness -- penalize fluff, redundancy, and filler hedges         (20 pts)

Rules:
- Treat WEB FACTS as the ground-truth reference set. Claims that contradict
  or are unsupported by them lose citation/coverage points.
- An empty or near-empty report scores below 10.
- A long, padded report scores below 60 even if otherwise accurate.
- Do not reward style over substance.

Reply with EXACTLY two lines and nothing else:
SCORE: <integer 0-100>
BREAKDOWN: <one short sentence naming the dominant strength and weakness>
"""


async def judge(
    report: str,
    topic: str,
    web_facts: List[Dict[str, str]],
) -> Tuple[float, str]:
    facts_block = "\n".join(
        f"- {r.get('title','')} :: {r.get('description','')}" for r in web_facts
    ) or "(no web facts available)"
    body = (
        f"TOPIC: {topic}\n\n"
        f"WEB FACTS:\n{facts_block}\n\n"
        f"REPORT:\n{report or '(empty)'}\n"
    )
    reply = await chat(
        [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": body},
        ],
        temperature=0.0,
    )
    score, breakdown = parse_score(reply)
    return score, breakdown or "(no breakdown)"
