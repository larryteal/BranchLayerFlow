"""Shared LLM + web-search helpers."""

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


def parse_phases(text: str) -> List[Dict[str, str]]:
    """Pull `PHASE: title | question` lines out of an LLM reply."""
    out: List[Dict[str, str]] = []
    for ln in text.splitlines():
        if "PHASE:" not in ln.upper():
            continue
        rest = ln.partition(":")[2] if ":" in ln else ln
        # tolerate "PHASE 1:" etc.
        rest = re.sub(r"^[\sPHASEphase\d.):-]+", "", rest).strip()
        if "|" not in rest:
            continue
        title, _, question = rest.partition("|")
        title = title.strip(" -*\"'")
        question = question.strip(" -*\"'")
        if title and question:
            out.append({"title": title, "question": question})
    return out
