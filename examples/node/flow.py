"""Cross-cutting retry + fallback expressed by subclassing BaseAgent.

BLF intentionally has no built-in retry — instead the framework exposes a
seam (`_takeover`) where you wrap the user-defined `takeover` with whatever
control-flow you want. Here we add a `RetryableAgent` base class; concrete
agents inherit from it and only need to write the actual work.
"""

from typing import Any, Optional

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


class RetryableAgent(BaseAgent):
    """Reusable mixin: retry `takeover` up to `meta.max_retries` times,
    then call `fallback` if every attempt raised."""

    def fallback(self, store: Any, error: Exception) -> None:
        raise error

    def _takeover(self, store: Any) -> None:
        last_error: Optional[Exception] = None
        for attempt in range(getattr(self.meta, "max_retries", 1)):
            try:
                self.takeover(store)
                return
            except Exception as exc:
                last_error = exc
                print(f"[{self.meta.name}] attempt {attempt + 1} failed: {exc}")
        assert last_error is not None
        self.fallback(store, last_error)


class SummarizeAgent(RetryableAgent):
    def takeover(self, store: Any) -> None:
        text = store["data"]
        store["summary"] = call_llm(
            f"Summarize this text in 10 words or less:\n{text}"
        )

    def fallback(self, store: Any, error: Exception) -> None:
        store["summary"] = "There was an error processing your request."


def build_summarize_flow() -> BaseFlow:
    summarize = SummarizeAgent(
        meta=BaseMeta(name="summarize", max_retries=3),
    )
    return BaseFlow(meta=BaseMeta(name="summarize_flow"), branches=(summarize,))
