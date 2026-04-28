import os
from typing import List, Dict, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def chat_completion(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    resp = _get_client().chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content
