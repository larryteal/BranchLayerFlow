"""The agent we expose over A2A. Intentionally simple: ask -> answer."""

from collections import deque
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


class AnswerAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["answer"] = call_llm(
            f"Answer concisely (one paragraph): {store['question']}"
        )


def answer_question(question: str) -> str:
    flow = BaseFlow(meta=BaseMeta(name="answer_flow"),
                    branches=(AnswerAgent(meta=BaseMeta(name="answer")),))
    store = {"question": question, "answer": ""}
    deque(flow(store=store), maxlen=0)
    return store["answer"]
