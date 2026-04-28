import os
from typing import Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def call_llm(prompt: str, model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content


def fake_calculator(expression: str) -> str:
    """A tiny deterministic 'tool' so the demo runs without external services."""
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as exc:
        return f"<error: {exc}>"
