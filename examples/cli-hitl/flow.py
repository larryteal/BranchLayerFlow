"""CLI HITL: generate a joke; ask user to approve.

  TopicAgent     (read topic once)
        |
        v
  GenerateAgent  (write a joke; uses prior rejections as context)
        |
        v
  ReviewAgent    (ask user; if rejected, loop back to GenerateAgent)
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


class TopicAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["topic"] = store.get("topic") or input("Topic: ").strip() or "branchless cats"
        store["rejected"] = []

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["generate"],)


class GenerateAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        prior = "\n".join(f"- {j}" for j in store["rejected"]) or "(none)"
        store["candidate"] = call_llm(
            f"Topic: {store['topic']}\n\nPrior jokes the user rejected:\n{prior}\n\n"
            "Write ONE short joke. Different angle than the rejected ones."
        )
        print(f"\n{store['candidate']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["review"],)


class ReviewAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        try:
            ans = input("Approve? (y/n): ").strip().lower()
        except EOFError:
            ans = "y"
        store["approved"] = ans.startswith("y")
        if not store["approved"]:
            store["rejected"].append(store["candidate"])

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return () if store["approved"] else (self.successors["generate"],)


def build_joke_flow() -> BaseFlow:
    t = TopicAgent(meta=BaseMeta(name="topic"))
    g = GenerateAgent(meta=BaseMeta(name="generate"))
    r = ReviewAgent(meta=BaseMeta(name="review"))
    t >> g
    g >> r
    r >> g
    return BaseFlow(meta=BaseMeta(name="joke_flow"), branches=(t,))
