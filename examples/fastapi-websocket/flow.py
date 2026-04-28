"""Single async chat agent that streams chunks to a WebSocket via store['ws_send']."""

import os
from typing import Any, List, Dict, Optional, Tuple

from branchlayerflow import AsyncBaseAgent, AsyncBaseFlow, BaseMeta
from openai import AsyncOpenAI


_client: Optional[AsyncOpenAI] = None


def _c() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


class StreamReplyAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        send = store["ws_send"]
        store["messages"].append({"role": "user", "content": store["user_text"]})
        stream = await _c().chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            messages=store["messages"],
            stream=True,
        )
        accum = []
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                accum.append(delta)
                await send(delta)
        await send("[[END]]")
        store["messages"].append({"role": "assistant", "content": "".join(accum)})


def build_chat_flow() -> AsyncBaseFlow:
    return AsyncBaseFlow(
        meta=BaseMeta(name="ws_chat"),
        branches=(StreamReplyAgent(meta=BaseMeta(name="reply")),),
    )
