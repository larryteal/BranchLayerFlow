"""Three-stage workflow whose every agent + flow is wrapped with `traced`."""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from tracer import Sink, traced


class FetchAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["data"] = list(range(10))

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["double"],)


class DoubleAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["data"] = [x * 2 for x in store["data"]]

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["sum"],)


class SumAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["total"] = sum(store["data"])


def build_traced_flow(sink: Sink) -> BaseFlow:
    F = traced(FetchAgent, sink)
    D = traced(DoubleAgent, sink)
    S = traced(SumAgent, sink)
    f = F(meta=BaseMeta(name="fetch"))
    d = D(meta=BaseMeta(name="double"))
    s = S(meta=BaseMeta(name="sum"))
    f >> d
    d >> s
    Flow = traced(BaseFlow, sink)
    return Flow(meta=BaseMeta(name="traced_flow"), branches=(f,))
