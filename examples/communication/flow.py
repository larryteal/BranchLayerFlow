"""Three agents communicating only through the shared `store`.

  InputAgent       (collects one text)
       |
       v
  CounterAgent     (updates running totals)
       |
       v
  ReporterAgent    (prints stats; loops back to InputAgent or terminates)

There are no direct calls between agents — each one only reads and
writes `store`. The store IS the communication channel; `handoff`
just decides who runs next.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta


class InputAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        try:
            text = input("Text (q to quit): ").strip()
        except EOFError:
            text = "q"
        store["last"] = text

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["last"].lower() == "q":
            return ()
        return (self.successors["count"],)


class CounterAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store.setdefault("totals", {"texts": 0, "words": 0})
        store["totals"]["texts"] += 1
        store["totals"]["words"] += len(store["last"].split())

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["report"],)


class ReporterAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        t = store["totals"]
        avg = t["words"] / t["texts"] if t["texts"] else 0.0
        print(f"  texts={t['texts']}  words={t['words']}  avg_words/text={avg:.2f}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["input"],)


def build_stats_flow() -> BaseFlow:
    inp = InputAgent(meta=BaseMeta(name="input"))
    cnt = CounterAgent(meta=BaseMeta(name="count"))
    rep = ReporterAgent(meta=BaseMeta(name="report"))
    inp >> cnt
    cnt >> rep
    rep >> inp
    return BaseFlow(meta=BaseMeta(name="stats_flow"), branches=(inp,))
