"""One-round adversarial debate.

  AdvocateForAgent      -> writes the case FOR
        |
        v
  AdvocateAgainstAgent  -> reads the FOR case and writes a rebuttal/AGAINST
        |
        v
  JudgeAgent            -> reads both, picks the winner with reasoning
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


class AdvocateForAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["pro"] = call_llm(
            f"Argue FOR the claim: {store['claim']!r}. Write 3 short paragraphs "
            "with specific reasoning and evidence."
        )
        print(f"=== FOR ===\n{store['pro']}\n")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["against"],)


class AdvocateAgainstAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["con"] = call_llm(
            f"Read the following argument FOR the claim {store['claim']!r}, "
            "then write 3 short paragraphs AGAINST the claim that rebut its points "
            "and present counter-evidence.\n\n"
            f"FOR ARGUMENT:\n{store['pro']}"
        )
        print(f"=== AGAINST ===\n{store['con']}\n")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["judge"],)


class JudgeAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["verdict"] = call_llm(
            f"You are an impartial judge. Read both arguments about the claim "
            f"{store['claim']!r}. Pick the stronger argument (FOR or AGAINST) "
            "and explain in 2 short paragraphs why.\n\n"
            f"FOR:\n{store['pro']}\n\nAGAINST:\n{store['con']}"
        )
        print(f"=== VERDICT ===\n{store['verdict']}")


def build_debate_flow() -> BaseFlow:
    pro = AdvocateForAgent(meta=BaseMeta(name="for"))
    con = AdvocateAgainstAgent(meta=BaseMeta(name="against"))
    judge = JudgeAgent(meta=BaseMeta(name="judge"))
    pro >> con
    con >> judge
    return BaseFlow(meta=BaseMeta(name="debate_flow"), branches=(pro,))
