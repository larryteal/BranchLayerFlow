import os
from typing import List, Dict, Optional

import yaml
from openai import OpenAI


_client: Optional[OpenAI] = None


def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(model=model, messages=messages).choices[0].message.content


def parse_action(text: str) -> Optional[dict]:
    """Find a YAML object containing a `tool` key. Tries fenced blocks first,
    then the whole text as a fallback."""
    candidates = []
    if "```" in text:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            body = parts[i]
            for tag in ("yaml", "yml", "json"):
                if body.startswith(tag):
                    body = body[len(tag):]
                    break
            candidates.append(body)
    candidates.append(text)
    for body in candidates:
        try:
            obj = yaml.safe_load(body)
        except yaml.YAMLError:
            continue
        if not isinstance(obj, dict):
            continue
        if "tool" in obj:
            return obj
        # tolerate one level of wrapping (e.g. {"action": {"tool": ...}})
        for value in obj.values():
            if isinstance(value, dict) and "tool" in value:
                return value
    return None
