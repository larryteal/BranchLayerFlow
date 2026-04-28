import os
from typing import List, Dict, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(model=model, messages=messages).choices[0].message.content


def strip_sql_fence(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            body = parts[i]
            if body.startswith("sql"):
                body = body[3:]
            return body.strip().rstrip(";")
    return text.strip().rstrip(";")
