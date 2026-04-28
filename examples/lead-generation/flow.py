"""Four-stage sales pipeline.

  ScrapeAgent     (load sample leads)
       |
       v
  EnrichAgent     (add funding/stack/size by LLM stub)
       |
       v
  ScoreAgent      (1-10 score per lead based on title/role)
       |
       v
  PersonaliseAgent (cold email for leads scoring >= 6)
"""

import re
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import SAMPLE_LEADS, chat


SCORE_RE = re.compile(r"\b([1-9]|10)\b")


class ScrapeAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["leads"] = [dict(l) for l in SAMPLE_LEADS]
        print(f"scraped {len(store['leads'])} leads")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["enrich"],)


class EnrichAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        for lead in store["leads"]:
            extra = chat([
                {"role": "system", "content": (
                    "Reply with three short labels separated by `; ` describing a "
                    "plausible funding stage, primary tech stack, and rough team size "
                    "for the company. Make it up plausibly; this is a demo."
                )},
                {"role": "user", "content": f"Company: {lead['company']}"},
            ])
            lead["enrichment"] = extra.strip()

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["score"],)


class ScoreAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        for lead in store["leads"]:
            reply = chat([
                {"role": "system", "content": (
                    "Score the lead 1-10 for fit as a buyer of a multi-agent "
                    "orchestration framework. Reply with the integer and one "
                    "short sentence."
                )},
                {"role": "user", "content": str(lead)},
            ])
            m = SCORE_RE.search(reply)
            lead["score"] = int(m.group(1)) if m else 0
            lead["score_reason"] = reply.strip()

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["personalise"],)


class PersonaliseAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        for lead in store["leads"]:
            if lead["score"] >= 6:
                lead["email"] = chat([
                    {"role": "system", "content": (
                        "Write a 3-sentence cold email pitching a multi-agent "
                        "orchestration framework. Specific to the recipient. No fluff."
                    )},
                    {"role": "user", "content": str(lead)},
                ])
        for lead in store["leads"]:
            print(f"\n{lead['name']} ({lead['title']} @ {lead['company']}) score={lead['score']}")
            if "email" in lead:
                print(f"  EMAIL:\n  {lead['email']}")


def build_lead_flow() -> BaseFlow:
    scrape = ScrapeAgent(meta=BaseMeta(name="scrape"))
    enrich = EnrichAgent(meta=BaseMeta(name="enrich"))
    score = ScoreAgent(meta=BaseMeta(name="score"))
    pers = PersonaliseAgent(meta=BaseMeta(name="personalise"))
    scrape >> enrich
    enrich >> score
    score >> pers
    return BaseFlow(meta=BaseMeta(name="lead_flow"), branches=(scrape,))
