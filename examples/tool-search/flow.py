"""Search-then-analyse pipeline.

  InputAgent     (read query + result count)
       |
       v
  SearchAgent    (call the search tool)
       |
       v
  AnalyseAgent   (LLM summary + follow-up questions)
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from tool_search import search_web
from utils import chat


class InputAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["query"] = store.get("query") or input("Search query: ").strip()
        store["num"] = store.get("num", 5)

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["search"],)


class SearchAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["results"] = search_web(store["query"], store["num"])
        for r in store["results"]:
            print(f"  {r['title']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["analyse"],)


class AnalyseAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        body = "\n".join(f"- {r['title']}: {r['snippet']}" for r in store["results"])
        store["analysis"] = chat([
            {"role": "system", "content": "You are a search-results analyst."},
            {"role": "user", "content": (
                f"Query: {store['query']}\n\nResults:\n{body}\n\n"
                "Write a short summary (3 sentences) and suggest 3 follow-up questions."
            )},
        ])
        print(f"\n{store['analysis']}")


def build_search_flow() -> BaseFlow:
    inp = InputAgent(meta=BaseMeta(name="input"))
    search = SearchAgent(meta=BaseMeta(name="search"))
    analyse = AnalyseAgent(meta=BaseMeta(name="analyse"))
    inp >> search
    search >> analyse
    return BaseFlow(meta=BaseMeta(name="search_flow"), branches=(inp,))
