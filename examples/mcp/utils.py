import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI


_client: Optional[AsyncOpenAI] = None


async def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = await _client.chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content


@asynccontextmanager
async def open_mcp_session():
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).parent / "server.py")],
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def list_tools_str(session: ClientSession) -> str:
    tools = (await session.list_tools()).tools
    return "\n".join(
        f"  - {t.name}({json.dumps(t.inputSchema.get('properties', {}))})"
        for t in tools
    )


async def call_tool(session: ClientSession, name: str, args: Dict[str, Any]) -> str:
    result = await session.call_tool(name, args)
    return "\n".join(getattr(c, "text", str(c)) for c in result.content)
