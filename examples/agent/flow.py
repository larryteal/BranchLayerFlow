"""Research agent loop.

  DecideAgent       -- look at notes; emit either `search: <q>` or `answer`
        |
        +--[search]--> SearchAgent --> DecideAgent (loop)
        +--[answer]--> AnswerAgent --> ()
"""

import re
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm, fake_search


SEARCH_RE = re.compile(r"^\s*SEARCH:\s*(.+)", re.IGNORECASE)


class DecideAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        notes = "\n".join(f"- {n}" for n in store["notes"]) or "(none yet)"
        decision = call_llm(
            f"Question: {store['query']}\n\nNotes so far:\n{notes}\n\n"
            "Decide what to do next. Reply with EXACTLY one of:\n"
            "  SEARCH: <a focused web query>\n"
            "  ANSWER\n"
            "Choose ANSWER only if the notes already let you answer well."
        ).strip()
        store["decision"] = decision

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        m = SEARCH_RE.match(store["decision"])
        if m and len(store["notes"]) < self.meta.max_searches:
            store["pending_query"] = m.group(1).strip()
            return (self.successors["search"],)
        return (self.successors["answer"],)


class SearchAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        snippets = fake_search(store["pending_query"])
        store["notes"].append(f"[{store['pending_query']}]\n  " + "\n  ".join(snippets))
        print(f"[search] {store['pending_query']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["decide"],)


class AnswerAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        notes = "\n\n".join(store["notes"]) or "(none)"
        store["answer"] = call_llm(
            f"Question: {store['query']}\n\nNotes:\n{notes}\n\n"
            "Write the final answer in one short paragraph."
        )
        print(f"\n=== Answer ===\n{store['answer']}")


def build_research_flow() -> BaseFlow:
    decide = DecideAgent(meta=BaseMeta(name="decide", max_searches=3))
    search = SearchAgent(meta=BaseMeta(name="search"))
    answer = AnswerAgent(meta=BaseMeta(name="answer"))
    decide >> search
    decide >> answer
    search >> decide
    return BaseFlow(meta=BaseMeta(name="research_flow"), branches=(decide,))
