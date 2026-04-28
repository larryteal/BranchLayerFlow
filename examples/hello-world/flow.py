from typing import Any

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


class AnswerAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["answer"] = call_llm(store["question"])


def build_qa_flow() -> BaseFlow:
    answer = AnswerAgent(meta=BaseMeta(name="answer"))
    return BaseFlow(meta=BaseMeta(name="qa_flow"), branches=(answer,))
