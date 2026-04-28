"""Search tool. Real backend uses SerpAPI; falls back to canned results."""

import os
from typing import List


def search_web(query: str, num: int = 5) -> List[dict]:
    if os.environ.get("SERPAPI_API_KEY"):
        from serpapi import GoogleSearch  # type: ignore
        results = GoogleSearch({
            "q": query, "api_key": os.environ["SERPAPI_API_KEY"], "num": num,
        }).get_dict().get("organic_results", [])[:num]
        return [{"title": r.get("title"), "snippet": r.get("snippet"), "link": r.get("link")}
                for r in results]
    # offline fallback
    return [
        {"title": f"Result {i+1} for {query!r}",
         "snippet": f"Mock snippet #{i+1} containing information about {query}.",
         "link": f"https://example.com/{i+1}"}
        for i in range(num)
    ]
