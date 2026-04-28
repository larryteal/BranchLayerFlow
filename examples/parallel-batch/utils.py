import os
from typing import Optional

from anthropic import AsyncAnthropic


_client: Optional[AsyncAnthropic] = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


async def call_llm(prompt: str, model: str = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")) -> str:
    msg = await _get_client().messages.create(
        model=model,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if block.type == "text")
