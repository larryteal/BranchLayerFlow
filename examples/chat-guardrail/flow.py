"""Travel-only chatbot.

  InputAgent     (read user query)
        |
        v
  GuardAgent     (basic + LLM-based topic check)
        |
        +--[reject]--> InputAgent           # ask again
        +--[accept]--> AdvisorAgent --> InputAgent
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat_completion


class InputAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        try:
            store["query"] = input("Travel question (exit to quit): ").strip()
        except EOFError:
            store["query"] = "exit"

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return () if store["query"].lower() == "exit" else (self.successors["guard"],)


class GuardAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        q = store["query"]
        if not q or len(q) < 3:
            store["verdict"] = ("reject", "Please ask a fuller travel question.")
            return
        verdict = chat_completion([
            {"role": "system", "content": (
                "You are a topic classifier. Reply with exactly one word: "
                "TRAVEL if the query is about travel destinations, trip planning, "
                "accommodations, transport, packing, or tourism; OFFTOPIC otherwise."
            )},
            {"role": "user", "content": q},
        ]).strip().upper()
        if verdict.startswith("TRAVEL"):
            store["verdict"] = ("accept", None)
        else:
            store["verdict"] = ("reject", "I only answer travel questions. Try again.")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        outcome, msg = store["verdict"]
        if outcome == "reject":
            print(f"[guard] {msg}")
            return (self.successors["input"],)
        return (self.successors["advisor"],)


class AdvisorAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        reply = chat_completion([
            {"role": "system", "content": "You are a concise travel advisor."},
            {"role": "user", "content": store["query"]},
        ])
        print(f"Advisor: {reply}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["input"],)


def build_guardrail_flow() -> BaseFlow:
    inp = InputAgent(meta=BaseMeta(name="input"))
    guard = GuardAgent(meta=BaseMeta(name="guard"))
    advisor = AdvisorAgent(meta=BaseMeta(name="advisor"))
    inp >> guard
    guard >> inp
    guard >> advisor
    advisor >> inp
    return BaseFlow(meta=BaseMeta(name="guardrail_flow"), branches=(inp,))
