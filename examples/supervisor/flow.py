"""Inner unreliable researcher wrapped by a supervisor.

  ResearchFlow                  <-- a sub-flow itself
    +-- SearchAgent  (gather web snippets into store)
    +-- AnswerAgent  (write an answer; intentionally unreliable)

  SupervisorAgent (after ResearchFlow runs)
        |
        +-- approve  -> ()                     (terminate)
        +-- reject   -> ResearchFlow again     (try again)

The supervisor sits OUTSIDE the inner flow. It treats the inner Flow
as just another agent it can re-summon — which is exactly what
"Flow IS Agent" buys you.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm, fake_search, maybe_garble


class SearchAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["snippet"] = fake_search(store["query"])

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["answer"],)


class AnswerAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        good = call_llm(
            f"Question: {store['query']}\n\nContext:\n{store['snippet']}\n\n"
            "Write a one-paragraph answer."
        )
        store["answer"] = maybe_garble(good)


class SupervisorAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        verdict = call_llm(
            "Reply with one word: GOOD if the following answer is coherent and "
            "addresses the question, BAD otherwise.\n\n"
            f"Question: {store['query']}\nAnswer: {store['answer']}"
        ).strip().upper()
        store["verdict"] = "GOOD" if verdict.startswith("GOOD") else "BAD"
        store["attempts"] = store.get("attempts", 0) + 1
        print(f"[supervisor #{store['attempts']}] verdict={store['verdict']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["verdict"] == "GOOD" or store["attempts"] >= 4:
            print(f"\nFINAL: {store['answer']}")
            return ()
        return (self.successors["research"],)


class ResearchFlow(BaseFlow):
    """Closing rite hands off to the supervisor (or whatever was registered)."""
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return tuple(self.successors.values())[:1] or None


def build_supervised_flow() -> BaseFlow:
    search = SearchAgent(meta=BaseMeta(name="search"))
    answer = AnswerAgent(meta=BaseMeta(name="answer"))
    search >> answer
    research = ResearchFlow(meta=BaseMeta(name="research"), branches=(search,))

    supervisor = SupervisorAgent(meta=BaseMeta(name="supervisor"))
    research >> supervisor
    supervisor >> research
    return BaseFlow(meta=BaseMeta(name="supervised_flow"), branches=(research,))
