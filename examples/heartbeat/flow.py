"""Outer monitor with an inner email flow.

Layout:
  HeartbeatFlow
    +-- WaitAgent       (sleep + count cycle)
    +-- (handoff -> InboxFlow each cycle until cycle == max)

  InboxFlow
    +-- CheckAgent      (fetch mail; if empty, hand off back up via empty handoff)
    +-- SummariseAgent  (LLM summary per message)
"""

import time
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm, fake_inbox


# ----- Inner flow -----

class CheckAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["inbox"] = fake_inbox()
        print(f"  inbox -> {len(store['inbox'])} message(s)")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["summary"],) if store["inbox"] else ()


class SummaryAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        for msg in store["inbox"]:
            summary = call_llm(f"Summarise in 8 words: {msg}")
            store.setdefault("processed", []).append({"msg": msg, "summary": summary})
            print(f"   -> {summary}")


class InboxFlow(BaseFlow):
    """Closing rite hands off back to the wait agent so the heartbeat ticks again."""
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return tuple(self.successors.values())[:1] or None


def build_inbox_flow() -> InboxFlow:
    chk = CheckAgent(meta=BaseMeta(name="check"))
    sm = SummaryAgent(meta=BaseMeta(name="summary"))
    chk >> sm
    return InboxFlow(meta=BaseMeta(name="inbox_flow"), branches=(chk,))


# ----- Outer monitor -----

class WaitAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["cycle"] = store.get("cycle", 0) + 1
        print(f"\n[heartbeat #{store['cycle']}]")
        time.sleep(store["interval"])

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["cycle"] >= store["max_cycles"]:
            return ()
        return (self.successors["inbox_flow"],)


def build_heartbeat_flow() -> BaseFlow:
    wait = WaitAgent(meta=BaseMeta(name="wait"))
    inbox = build_inbox_flow()
    wait >> inbox
    inbox >> wait  # InboxFlow.handoff returns wait
    return BaseFlow(meta=BaseMeta(name="heartbeat_flow"), branches=(wait,))
