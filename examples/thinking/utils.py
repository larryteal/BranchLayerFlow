import os
from typing import Optional

from anthropic import Anthropic


_client: Optional[Anthropic] = None


def call_llm(prompt: str, model: str = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")) -> str:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=600.0)
    msg = _client.messages.create(
        model=model,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if block.type == "text")
