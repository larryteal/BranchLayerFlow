"""Shared LLM + web-search helpers."""

import os
import re
from typing import Dict, List, Optional, Tuple

import httpx
from openai import AsyncOpenAI


WEB_SEARCH_BASE = os.environ.get("WEB_SEARCH_URL", "https://web-search-cat.lessx.xyz")

_llm: Optional[AsyncOpenAI] = None


async def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kw,
) -> str:
    global _llm
    if _llm is None:
        kwargs = {"api_key": os.environ["OPENAI_API_KEY"]}
        if base := os.environ.get("OPENAI_BASE_URL"):
            kwargs["base_url"] = base
        _llm = AsyncOpenAI(**kwargs)
    if temperature is not None:
        kw["temperature"] = temperature
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


def parse_score(text: str) -> Tuple[float, str]:
    """Pull `SCORE: <num>` and `BREAKDOWN: <line>` out of a judge reply.

    Tolerates extra prose. Returns (score, one-line breakdown).
    """
    score = -1.0
    m = re.search(r"SCORE\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if m:
        try:
            score = float(m.group(1))
        except ValueError:
            pass
    breakdown = ""
    bm = re.search(r"BREAKDOWN\s*[:=]\s*(.+?)(?:\n|$)", text, re.IGNORECASE | re.DOTALL)
    if bm:
        breakdown = bm.group(1).strip().splitlines()[0][:200]
    return score, breakdown
