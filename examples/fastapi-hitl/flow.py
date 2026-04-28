"""HITL: process -> wait-for-approval -> (done | reprocess).

The waiting agent blocks on a per-job `threading.Event` set by an HTTP
endpoint. Approve resolves the loop; reject loops back to the processor.
"""

import threading
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta


class ProcessAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["round"] = store.get("round", 0) + 1
        # Trivial fake processing — caps + reverse for round N
        text = store["text"].upper() if store["round"] % 2 == 1 else store["text"][::-1]
        store["draft"] = f"[round {store['round']}] {text}"
        store["sink"]({"stage": "draft_ready", "draft": store["draft"]})

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["wait"],)


class WaitAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["sink"]({"stage": "awaiting_review"})
        ev: threading.Event = store["review_event"]
        ev.wait()
        ev.clear()

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["last_decision"] == "approve":
            store["sink"]({"stage": "approved", "final": store["draft"]})
            return ()
        return (self.successors["process"],)


def build_hitl_flow() -> BaseFlow:
    p = ProcessAgent(meta=BaseMeta(name="process"))
    w = WaitAgent(meta=BaseMeta(name="wait"))
    p >> w
    w >> p
    return BaseFlow(meta=BaseMeta(name="hitl_flow"), branches=(p,))
