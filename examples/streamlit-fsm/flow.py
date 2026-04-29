"""Image-gen FSM driven one transition per Streamlit interaction.

Each `step(store)` call advances the FSM by running exactly one BLF
agent, picked from `store["state"]`. Streamlit owns the rendering loop;
BLF owns the state transitions.

States:
  input       -> waiting for prompt (UI only)
  generating  -> run GenerateAgent
  review      -> waiting for the user (UI only); decision triggers next step
  final       -> done (UI only)
"""

from collections import deque
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import generate_image_b64


class GenerateAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["image_b64"] = generate_image_b64(store["prompt"])
        store["state"] = "review"


class DecisionAgent(BaseAgent):
    """Reads `store['decision']` (set by the UI) and routes."""

    def takeover(self, store: Any) -> None:
        decision = store.pop("decision", None)
        if decision == "approve":
            store["state"] = "final"
        elif decision == "reject":
            store["state"] = "generating"

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["state"] == "generating":
            return (self.successors["generate"],)
        return ()


def step(store: Any) -> None:
    """Advance the FSM by one transition based on the current state."""
    state = store.get("state", "input")
    if state == "generating":
        deque(BaseFlow(
            meta=BaseMeta(name="gen_flow"),
            branches=(GenerateAgent(meta=BaseMeta(name="generate")),),
        )(store=store), maxlen=0)
    elif state == "review":
        gen = GenerateAgent(meta=BaseMeta(name="generate"))
        dec = DecisionAgent(meta=BaseMeta(name="decision"))
        dec >> gen
        deque(BaseFlow(
            meta=BaseMeta(name="dec_flow"),
            branches=(dec,),
        )(store=store), maxlen=0)
    # input / final: nothing to advance
