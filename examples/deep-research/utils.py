import os
import re
from typing import List, Dict, Optional

from openai import AsyncOpenAI


_client: Optional[AsyncOpenAI] = None


async def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = await _client.chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content


def split_lines(text: str, n: int) -> List[str]:
    """Best-effort split of an LLM bullet list into N items."""
    items = re.findall(r"^\s*(?:[-*0-9.]\s*)?(.+?)$", text.strip(), flags=re.MULTILINE)
    items = [i.strip(" .-*") for i in items if i.strip()]
    return items[:n]


async def fake_search(query: str) -> List[str]:
    """Stand-in. Plug in a real backend if you have one."""
    if os.environ.get("USE_REAL_SEARCH"):
        from serpapi import GoogleSearch  # type: ignore
        results = GoogleSearch({"q": query, "api_key": os.environ["SERPAPI_API_KEY"]}).get_dict()
        return [r.get("snippet", "") for r in results.get("organic_results", [])[:5]]
    return [
        f"Snippet 1 about {query!r}: a relevant fact and supporting context.",
        f"Snippet 2 about {query!r}: a counter-perspective worth noting.",
        f"Snippet 3 about {query!r}: extended detail and a citation pointer.",
    ]
