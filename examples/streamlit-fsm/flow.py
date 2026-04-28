"""Image-gen FSM driven one transition per Streamlit interaction.

Each `tick(store)` call advances the FSM by exactly one BLF agent.
Streamlit owns the rendering loop; BLF owns the state transitions.
"""

from collections import deque
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import generate_image_b64


class GenerateAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["image_b64"] = generate_image_b64(store["prompt"])
        store["state"] = "review"


class ReviewAgent(BaseAgent):
    """No-op holder; UI sets store['decision'] and re-runs."""

    def takeover(self, store: Any) -> None:
        if "decision" not in store:
            store["state"] = "review"  # waiting for the user

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store.get("decision") == "approve":
            store["state"] = "final"
            return ()
        if store.get("decision") == "reject":
            store["state"] = "generating"
            store.pop("decision", None)
            return (self.successors["generate"],)
        return ()


def build_imgflow() -> BaseFlow:
    g = GenerateAgent(meta=BaseMeta(name="generate"))
    r = ReviewAgent(meta=BaseMeta(name="review"))
    g >> r
    r >> g
    return BaseFlow(meta=BaseMeta(name="imgflow"), branches=(g,))


def step(store: Any) -> None:
    """Drain the flow; each call advances until it next blocks for input."""
    deque(build_imgflow()(store=store), maxlen=0)
