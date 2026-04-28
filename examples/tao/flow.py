"""Thought-Action-Observation loop.

  ThoughtAgent      -- decides what to do next (or commits an answer)
        |
        v
  ActionAgent       -- executes the chosen tool action
        |
        v
  ObservationAgent  -- records the result; loops back to ThoughtAgent
                       unless the answer is final.
"""

import re
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm, fake_calculator


THINK_PROMPT = """You are solving a problem step by step.

PROBLEM:
{problem}

HISTORY OF (Thought, Action, Observation):
{history}

Write the next THOUGHT, then choose ONE of:
  ACTION: calc <expression>     (use the calculator)
  ACTION: finish <answer>       (commit your final answer)

Format your reply EXACTLY as:
THOUGHT: <one paragraph>
ACTION: <calc ... | finish ...>
"""


THOUGHT_RE = re.compile(r"THOUGHT:\s*(.+?)\nACTION:", re.DOTALL)
ACTION_RE = re.compile(r"ACTION:\s*(.+)", re.IGNORECASE)


class ThoughtAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store.setdefault("history", [])
        history = (
            "\n".join(
                f"  T: {t}\n  A: {a}\n  O: {o}"
                for (t, a, o) in store["history"]
            )
            or "(none)"
        )
        reply = call_llm(THINK_PROMPT.format(problem=store["problem"], history=history))
        store["pending_thought"] = (THOUGHT_RE.search(reply) or _empty()).group(1).strip()
        store["pending_action"] = (ACTION_RE.search(reply) or _empty()).group(1).strip()
        print(f"THOUGHT: {store['pending_thought']}")
        print(f"ACTION:  {store['pending_action']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["action"],)


def _empty():
    class _M:
        def group(self, _):
            return ""
    return _M()


class ActionAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        action = store["pending_action"]
        if action.startswith("calc "):
            result = fake_calculator(action[5:])
            store["pending_observation"] = f"calculator returned {result}"
        elif action.startswith("finish"):
            store["final"] = action[len("finish "):].strip()
            store["pending_observation"] = "(final answer committed)"
        else:
            store["pending_observation"] = f"unknown action: {action!r}"
        print(f"OBSERVE: {store['pending_observation']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["observe"],)


class ObservationAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["history"].append((
            store["pending_thought"],
            store["pending_action"],
            store["pending_observation"],
        ))

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if "final" in store or len(store["history"]) >= self.meta.max_cycles:
            return ()
        return (self.successors["think"],)


def build_tao_flow() -> BaseFlow:
    think = ThoughtAgent(meta=BaseMeta(name="think"))
    action = ActionAgent(meta=BaseMeta(name="action"))
    observe = ObservationAgent(meta=BaseMeta(name="observe", max_cycles=6))
    think >> action
    action >> observe
    observe >> think
    return BaseFlow(meta=BaseMeta(name="tao_flow"), branches=(think,))
