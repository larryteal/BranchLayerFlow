import os
from typing import Optional

from openai import AsyncOpenAI


_client: Optional[AsyncOpenAI] = None


async def call_llm(prompt: str, model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = await _client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
