"""Chain-of-thought reasoning via a self-looping agent.

Each iteration, the agent:
  1. Writes one short reasoning step.
  2. Decides whether to continue thinking or commit a final answer.

Loop = `handoff` returning `(self,)` until the agent emits "FINAL:".
This externalizes the reasoning loop instead of relying on the model's
internal context to drive multi-step inference.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


PROMPT_TEMPLATE = """You are solving a problem step by step.

PROBLEM:
{problem}

PRIOR REASONING:
{history}

Write the NEXT short reasoning step (one paragraph).
If you are confident in the final answer, end your message with a line
of the form `FINAL: <your answer>`.
"""


class ThinkAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store.setdefault("steps", [])
        history = "\n\n".join(f"Step {i}: {s}" for i, s in enumerate(store["steps"], 1)) or "(none)"
        step = call_llm(PROMPT_TEMPLATE.format(problem=store["problem"], history=history))
        store["steps"].append(step)
        print(f"--- Step {len(store['steps'])} ---\n{step}\n")
        if "FINAL:" in step:
            store["final"] = step.split("FINAL:", 1)[1].strip()
            store["done"] = True

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store.get("done") or len(store["steps"]) >= getattr(self.meta, "max_steps", 8):
            return ()
        return (self,)


def build_thinking_flow() -> BaseFlow:
    think = ThinkAgent(meta=BaseMeta(name="think", max_steps=8))
    return BaseFlow(meta=BaseMeta(name="thinking_flow"), branches=(think,))
