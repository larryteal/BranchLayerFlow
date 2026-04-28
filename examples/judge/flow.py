"""Generator <-> Judge evaluator-optimizer loop.

  GeneratorAgent -- writes a candidate description (uses prior feedback)
        |
        v
  JudgeAgent     -- scores it; if below threshold, loops back to generator
                    with feedback; otherwise terminates.
"""

import re
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


SCORE_RE = re.compile(r"score\s*[:=]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)


class GeneratorAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        feedback = store.get("feedback", "")
        prompt = (
            f"Write a 2-sentence product description for: {store['product']}.\n"
            f"Aim for clarity and persuasiveness."
        )
        if feedback:
            prompt += f"\n\nPrior version's feedback (incorporate it):\n{feedback}"
        store["candidate"] = call_llm(prompt)
        store["attempts"] = store.get("attempts", 0) + 1
        print(f"\n--- Attempt {store['attempts']} ---\n{store['candidate']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["judge"],)


class JudgeAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        review = call_llm(
            "Evaluate the following product description for clarity and "
            "persuasiveness. Give a single integer score from 1 to 10 on a "
            "line of the form `Score: <n>`, then a short paragraph of "
            "actionable feedback.\n\n"
            f"DESCRIPTION:\n{store['candidate']}"
        )
        match = SCORE_RE.search(review)
        score = float(match.group(1)) if match else 0.0
        store["score"] = score
        store["feedback"] = review
        print(f"[judge] score={score}\n{review}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["score"] >= self.meta.threshold or store["attempts"] >= self.meta.max_attempts:
            return ()
        return (self.successors["generator"],)


def build_judge_flow() -> BaseFlow:
    gen = GeneratorAgent(meta=BaseMeta(name="generator"))
    judge = JudgeAgent(meta=BaseMeta(name="judge", threshold=7.0, max_attempts=3))
    gen >> judge
    judge >> gen
    return BaseFlow(meta=BaseMeta(name="judge_flow"), branches=(gen,))
