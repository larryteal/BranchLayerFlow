"""Agent loop with a patch sub-flow.

  AgentAgent           -- decide which tool to call (LLM)
        |
        v
  ToolAgent            -- dispatch the tool call; if `patch_file`, hand off
                          to the PATCH SUB-FLOW instead of the inline tool.
        |
        +--[done]------> ()
        +--[continue]--> AgentAgent (loop)

  PatchSubFlow:
    ReadAgent -> ValidateAgent -> ApplyAgent
"""

from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

import tools
from utils import chat, parse_action


SYSTEM_PROMPT = """You are an autonomous coding agent. You have these tools:
  list_files                  -> {tool: list_files}
  grep_search(pattern)        -> {tool: grep_search, pattern: ...}
  read_file(path)             -> {tool: read_file, path: ...}
  patch_file(path, search, replace) -> {tool: patch_file, path: ..., search: ..., replace: ...}
  run_command(cmd)            -> {tool: run_command, cmd: ...}
  done(message)               -> {tool: done, message: ...}

You receive the user's TASK and a HISTORY of (action, result) pairs.
Reply with a single fenced YAML block giving exactly ONE next action.
Be concise; prefer running tests once you've made a change.
"""


class AgentAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        history = "\n".join(
            f"-- step {i} --\nACTION: {a}\nRESULT: {r[:600]}"
            for i, (a, r) in enumerate(store["history"], 1)
        ) or "(empty)"
        reply = chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"TASK:\n{store['task']}\n\nHISTORY:\n{history}"},
        ])
        store["pending_action"] = parse_action(reply) or {"tool": "done", "message": "could not parse action"}
        print(f"\n[step {len(store['history'])+1}] action: {store['pending_action']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["tool"],)


# ----- Patch sub-flow -----

class _ReadForPatch(BaseAgent):
    def takeover(self, store: Any) -> None:
        action = store["pending_action"]
        store["_patch"] = {
            "path": action["path"],
            "search": action["search"],
            "replace": action["replace"],
            "current": tools.read_file(Path(store["root"]), action["path"]),
        }

    def handoff(self, s):
        return (self.successors["validate"],)


class _ValidatePatch(BaseAgent):
    def takeover(self, store: Any) -> None:
        p = store["_patch"]
        count = p["current"].count(p["search"])
        p["valid"] = count == 1
        p["validation_msg"] = "OK" if p["valid"] else f"search string occurs {count} time(s)"

    def handoff(self, s):
        return (self.successors["apply"],)


class _ApplyPatch(BaseAgent):
    def takeover(self, store: Any) -> None:
        p = store["_patch"]
        if not p["valid"]:
            store["pending_result"] = f"PATCH ERROR: {p['validation_msg']}"
            return
        store["pending_result"] = tools.patch_file(
            Path(store["root"]), p["path"], p["search"], p["replace"]
        )


def build_patch_subflow() -> BaseFlow:
    r = _ReadForPatch(meta=BaseMeta(name="read_for_patch"))
    v = _ValidatePatch(meta=BaseMeta(name="validate"))
    a = _ApplyPatch(meta=BaseMeta(name="apply"))
    r >> v
    v >> a
    return BaseFlow(meta=BaseMeta(name="patch_subflow"), branches=(r,))


# ----- Main tool dispatcher -----

class ToolAgent(BaseAgent):
    def __init__(self, *args, patch_subflow: BaseFlow, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._patch = patch_subflow

    def takeover(self, store: Any) -> None:
        action = store["pending_action"]
        tool = action.get("tool", "done")
        root = Path(store["root"])
        if tool == "list_files":
            store["pending_result"] = "\n".join(tools.list_files(root))
        elif tool == "grep_search":
            store["pending_result"] = "\n".join(tools.grep_search(root, action.get("pattern", "")))
        elif tool == "read_file":
            store["pending_result"] = tools.read_file(root, action["path"])
        elif tool == "run_command":
            store["pending_result"] = tools.run_command(root, action["cmd"])
        elif tool == "patch_file":
            from collections import deque
            deque(self._patch(store=store), maxlen=0)  # writes pending_result itself
        elif tool == "done":
            store["pending_result"] = tools.done(action.get("message", ""))
            store["finished"] = True
        else:
            store["pending_result"] = f"unknown tool: {tool}"
        store["history"].append((str(action), store["pending_result"]))

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store.get("finished") or len(store["history"]) >= self.meta.max_steps:
            return ()
        return (self.successors["agent"],)


def build_coding_agent_flow(max_steps: int = 12) -> BaseFlow:
    patch = build_patch_subflow()
    agent = AgentAgent(meta=BaseMeta(name="agent"))
    tool = ToolAgent(meta=BaseMeta(name="tool", max_steps=max_steps), patch_subflow=patch)
    agent >> tool
    tool >> agent
    return BaseFlow(meta=BaseMeta(name="coding_agent_flow"), branches=(agent,))
