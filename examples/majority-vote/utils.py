import os
from typing import Optional

from anthropic import AsyncAnthropic


_client: Optional[AsyncAnthropic] = None


async def call_llm(prompt: str, model: str = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")) -> str:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = await _client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")
