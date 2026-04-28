"""Polite, domain-bounded crawler tool."""

import time
from collections import deque
from typing import List, Set
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def crawl(seed: str, max_pages: int = 5, delay: float = 0.5) -> List[dict]:
    domain = urlparse(seed).netloc
    seen: Set[str] = set()
    queue = deque([seed])
    pages: List[dict] = []
    while queue and len(pages) < max_pages:
        url, _ = urldefrag(queue.popleft())
        if url in seen or urlparse(url).netloc != domain:
            continue
        seen.add(url)
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "blf-crawler/0.1"})
            resp.raise_for_status()
        except requests.RequestException:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        text = " ".join(soup.stripped_strings)[:4000]
        pages.append({"url": url, "title": (soup.title.string if soup.title else url)[:200], "text": text})
        for a in soup.find_all("a", href=True):
            queue.append(urljoin(url, a["href"]))
        time.sleep(delay)
    return pages
