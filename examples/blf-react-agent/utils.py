"""Shared LLM + web-search/news helpers."""

import os
import re
from typing import Dict, List, Optional

import httpx
from openai import AsyncOpenAI


WEB_SEARCH_BASE = os.environ.get("WEB_SEARCH_URL", "https://web-search-cat.lessx.xyz")

_llm: Optional[AsyncOpenAI] = None


async def chat(messages: List[Dict[str, str]], model: Optional[str] = None, **kw) -> str:
    global _llm
    if _llm is None:
        kwargs = {"api_key": os.environ["OPENAI_API_KEY"]}
        if base := os.environ.get("OPENAI_BASE_URL"):
            kwargs["base_url"] = base
        _llm = AsyncOpenAI(**kwargs)
    resp = await _llm.chat.completions.create(
        model=model or os.environ.get("OPENAI_MODEL", "gpt-4o"),
        messages=messages,
        **kw,
    )
    return resp.choices[0].message.content


async def web_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.get(f"{WEB_SEARCH_BASE}/search", params={"q": query, "max": max_results})
        r.raise_for_status()
        return r.json().get("results", [])


async def news_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.get(f"{WEB_SEARCH_BASE}/news", params={"q": query, "max": max_results})
        r.raise_for_status()
        return r.json().get("results", [])


def parse_action(text: str) -> Optional[Dict]:
    """Pull the first {...} JSON object from `text`."""
    import json

    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None
