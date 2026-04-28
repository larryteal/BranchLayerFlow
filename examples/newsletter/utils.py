import os
from typing import List, Dict, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(model=model, messages=messages).choices[0].message.content


def search_topic(topic: str, n: int = 5) -> List[Dict[str, str]]:
    """DuckDuckGo search; returns raw result dicts."""
    if os.environ.get("OFFLINE"):
        return [
            {"title": f"Mock {i+1}: {topic}", "body": f"Sample snippet {i+1} about {topic}.", "href": "https://example.com"}
            for i in range(n)
        ]
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        return list(ddgs.text(topic, max_results=n))
