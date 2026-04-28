import os
from typing import List, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def call_llm(prompt: str, model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content


def fake_search(query: str) -> List[str]:
    """Stand-in web search — returns canned snippets so the demo runs offline.
    Set USE_REAL_SEARCH=1 with `serpapi` installed to swap in a real backend."""
    if os.environ.get("USE_REAL_SEARCH"):
        from serpapi import GoogleSearch  # type: ignore
        results = GoogleSearch({"q": query, "api_key": os.environ["SERPAPI_API_KEY"]}).get_dict()
        return [r.get("snippet", "") for r in results.get("organic_results", [])[:5]]
    return [
        f"Snippet 1 about {query!r}: relevant overview text.",
        f"Snippet 2 about {query!r}: a slightly more detailed factoid.",
        f"Snippet 3 about {query!r}: contradictory but plausible claim.",
    ]
