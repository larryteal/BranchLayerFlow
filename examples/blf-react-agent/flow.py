"""Tool-using reason->act->observe loop.

  ThinkAgent  -- if tool == finish -->  FinalizeAgent
       |
       v   else
  ActAgent  (web_search | news_search)
       |
       v
  ThinkAgent  (next iteration)

The `>>` topology is the entire control flow: `think >> act >> think` makes
the loop, `think >> finalize` is the exit edge. ThinkAgent.handoff just
picks which wired successor to return based on the parsed action.
"""

import json
from typing import Any, Optional, Tuple

from branchlayerflow import AsyncBaseAgent, AsyncBaseFlow, BaseMeta

from utils import chat, news_search, parse_action, web_search


SYSTEM_PROMPT = (
    "You are an autonomous research agent. Choose ONE tool per step.\n"
    "Available tools:\n"
    '  - web_search    args: {"query": "..."}\n'
    '  - news_search   args: {"query": "..."}\n'
    '  - finish        args: {"answer": "<final answer>"}\n'
    "Reply with ONLY a JSON object on a single line, no prose:\n"
    '  {"thought": "<short reasoning>", "tool": "<name>", "args": {...}}'
)


class ThinkAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store.setdefault("scratchpad", [])
        store.setdefault("step", 0)
        history = "\n\n".join(store["scratchpad"]) or "(empty)"
        reply = await chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Goal: {store['goal']}\n"
                f"Step: {store['step'] + 1} / {store['max_steps']}\n"
                f"Scratchpad:\n{history}"
            )},
        ])
        action = parse_action(reply) or {
            "thought": "(unparseable response, finishing)",
            "tool": "finish",
            "args": {"answer": reply.strip()},
        }
        store["last_action"] = action
        store["step"] += 1
        store["scratchpad"].append(
            f"Thought: {action.get('thought','')}\n"
            f"Action: {action.get('tool')} {json.dumps(action.get('args', {}), ensure_ascii=False)}"
        )
        print(f"\n[step {store['step']}] tool={action.get('tool')} args={action.get('args')}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        action = store["last_action"]
        if action.get("tool") == "finish" or store["step"] >= store["max_steps"]:
            return (self.successors["finalize"],)
        return (self.successors["act"],)


class ActAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        action = store["last_action"]
        tool = action.get("tool")
        args = action.get("args", {})
        try:
            if tool == "web_search":
                rows = await web_search(args.get("query", ""), 10)
                obs = "\n".join(f"- {r.get('title','')}: {r.get('description','')}" for r in rows) or "(no results)"
            elif tool == "news_search":
                rows = await news_search(args.get("query", ""), 10)
                obs = "\n".join(f"- {r.get('title','')} [{r.get('source','')}]: {r.get('date','')}" for r in rows) or "(no results)"
            else:
                obs = f"unknown tool: {tool!r}"
        except Exception as e:
            obs = f"tool error: {e}"
        truncated = obs[:1500]
        store["scratchpad"].append(f"Observation:\n{truncated}")
        print(f"[obs]\n{truncated[:600]}{'...' if len(truncated) > 600 else ''}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["think"],)


class FinalizeAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        action = store.get("last_action") or {}
        if action.get("tool") == "finish":
            store["answer"] = action.get("args", {}).get("answer", "")
        else:
            store["answer"] = await chat([
                {"role": "system", "content": "Synthesize the scratchpad into a concise final answer to the goal."},
                {"role": "user", "content": f"Goal: {store['goal']}\n\nScratchpad:\n" + "\n\n".join(store["scratchpad"])},
            ])
        print(f"\n=== Answer ===\n{store['answer']}")


def build_react_agent_flow() -> AsyncBaseFlow:
    think = ThinkAgent(meta=BaseMeta(name="think"))
    act = ActAgent(meta=BaseMeta(name="act"))
    finalize = FinalizeAgent(meta=BaseMeta(name="finalize"))
    think >> act >> think  # the loop
    think >> finalize      # exit
    return AsyncBaseFlow(meta=BaseMeta(name="react"), branches=(think,))
