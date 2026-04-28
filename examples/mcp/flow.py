"""Agent that asks an MCP server which tool to call, then calls it.

  PlanAgent  (LLM picks a tool + args from MCP server's tool list)
       |
       v
  CallAgent  (invokes the tool over MCP and prints the result)
"""

import json
import re
from typing import Any, Optional, Tuple

from branchlayerflow import AsyncBaseAgent, AsyncBaseFlow, BaseMeta

from utils import call_tool, chat, list_tools_str, open_mcp_session


CALL_RE = re.compile(r"CALL:\s*(\w+)\s*(\{.*\})", re.DOTALL)


class PlanAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        async with open_mcp_session() as session:
            tools = await list_tools_str(session)
            store["tools_doc"] = tools
        reply = await chat([
            {"role": "system", "content": (
                "Pick ONE tool to answer the user's question. Reply EXACTLY:\n"
                "  CALL: <tool_name> {<json-args>}"
            )},
            {"role": "user", "content": f"Question: {store['question']}\n\nAvailable tools:\n{store['tools_doc']}"},
        ])
        m = CALL_RE.search(reply)
        if not m:
            raise RuntimeError(f"could not parse plan: {reply}")
        store["plan"] = {"tool": m.group(1), "args": json.loads(m.group(2))}
        print(f"plan: {store['plan']}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["call"],)


class CallAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        async with open_mcp_session() as session:
            store["result"] = await call_tool(session, store["plan"]["tool"], store["plan"]["args"])
        print(f"result: {store['result']}")


def build_mcp_flow() -> AsyncBaseFlow:
    p = PlanAgent(meta=BaseMeta(name="plan"))
    c = CallAgent(meta=BaseMeta(name="call"))
    p >> c
    return AsyncBaseFlow(meta=BaseMeta(name="mcp_flow"), branches=(p,))
