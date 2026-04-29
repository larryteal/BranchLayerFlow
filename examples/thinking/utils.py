import os
from typing import Optional

from anthropic import Anthropic


_client: Optional[Anthropic] = None


def call_llm(prompt: str, model: str = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")) -> str:
    """Streamed call so the HTTP connection stays warm during long thinking
    blocks (some Anthropic-compatible providers close idle connections
    mid-response otherwise)."""
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=600.0)
    text_parts = []
    thinking_parts = []
    with _client.messages.stream(
        model=model,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for event in stream:
            delta = getattr(event, "delta", None)
            if delta is None:
                continue
            kind = getattr(delta, "type", "")
            if kind == "text_delta":
                text_parts.append(delta.text)
            elif kind == "thinking_delta":
                thinking_parts.append(delta.thinking)
    return "".join(text_parts) or "".join(thinking_parts)
