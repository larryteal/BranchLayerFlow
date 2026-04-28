"""Crawl -> summarise pipeline.

  CrawlAgent     (fetch up to N pages from one domain)
       |
       v
  AnalyseAgent   (summary + topic tags via LLM, per page in parallel)
"""

from typing import Any, Optional, Tuple

from branchlayerflow import (
    AsyncBaseAgent, AsyncBaseFlow, AsyncParallelBaseFlow, BaseMeta,
)
import asyncio

from tool_crawl import crawl
from utils import chat


class CrawlAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        loop = asyncio.get_event_loop()
        store["pages"] = await loop.run_in_executor(
            None, crawl, store["seed"], store["max_pages"]
        )
        print(f"crawled {len(store['pages'])} pages")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        analysers = tuple(
            PageAnalyseAgent(meta=BaseMeta(name=f"analyse_{i}", page_index=i))
            for i in range(len(store["pages"]))
        )
        return (AsyncParallelBaseFlow(meta=BaseMeta(name="parallel_analyse"), branches=analysers),)


class PageAnalyseAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        loop = asyncio.get_event_loop()
        page = store["pages"][self.meta.page_index]
        analysis = await loop.run_in_executor(None, lambda: chat([
            {"role": "system", "content": "Summarise the page in 2 sentences and list 3 topic tags."},
            {"role": "user", "content": f"URL: {page['url']}\nTITLE: {page['title']}\n\n{page['text']}"},
        ]))
        store.setdefault("analyses", []).append({"url": page["url"], "analysis": analysis})
        print(f"  done: {page['url']}")


def build_crawl_flow() -> AsyncBaseFlow:
    return AsyncBaseFlow(
        meta=BaseMeta(name="crawl_flow"),
        branches=(CrawlAgent(meta=BaseMeta(name="crawl")),),
    )
