"""Curate -> Filter -> Summarise -> Format newsletter pipeline."""

import re
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat, search_topic


class CurateAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        all_results = []
        for topic in store["topics"]:
            for r in search_topic(topic, n=5):
                all_results.append({"topic": topic, **r})
        store["raw"] = all_results
        print(f"curated {len(all_results)} candidates")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["filter"],)


class FilterAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        candidates = "\n".join(
            f"{i}. [{r['topic']}] {r['title']}: {r['body'][:200]}"
            for i, r in enumerate(store["raw"])
        )
        reply = chat([
            {"role": "system", "content": (
                "Pick the 4 most newsworthy items. Reply with their indices, "
                "comma-separated, e.g. `2, 5, 8, 11`."
            )},
            {"role": "user", "content": candidates},
        ])
        idxs = [int(m) for m in re.findall(r"\d+", reply)][:4]
        store["picked"] = [store["raw"][i] for i in idxs if i < len(store["raw"])]

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["summarise"],)


class SummariseAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        for item in store["picked"]:
            item["blurb"] = chat([
                {"role": "system", "content": "Write a punchy 2-3 sentence newsletter blurb."},
                {"role": "user", "content": f"{item['title']}\n{item['body']}"},
            ])

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["format"],)


class FormatAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        lines = [f"# AI Weekly\n"]
        for item in store["picked"]:
            lines.append(f"## {item['title']}\n")
            lines.append(item["blurb"].strip() + "\n")
            if item.get("href"):
                lines.append(f"[Read more]({item['href']})\n")
        store["markdown"] = "\n".join(lines)
        print(store["markdown"])


def build_newsletter_flow() -> BaseFlow:
    curate = CurateAgent(meta=BaseMeta(name="curate"))
    filter_ = FilterAgent(meta=BaseMeta(name="filter"))
    summ = SummariseAgent(meta=BaseMeta(name="summarise"))
    fmt = FormatAgent(meta=BaseMeta(name="format"))
    curate >> filter_
    filter_ >> summ
    summ >> fmt
    return BaseFlow(meta=BaseMeta(name="newsletter_flow"), branches=(curate,))
