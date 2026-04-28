"""Outline -> Draft -> Style writing pipeline that publishes progress events."""

from typing import Any, Optional, Tuple

import yaml
from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


def _strip_fence(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            body = parts[1]
            if body.startswith("yaml"):
                body = body[4:]
            return body
    return text


def _publish(store: Any, stage: str, status: str = "running", **extra: Any) -> None:
    sink = store.get("sink")
    if sink is not None:
        sink({"stage": stage, "status": status, **extra})


class OutlineAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        _publish(store, "outline")
        raw = call_llm(
            f"Create an outline for an article on '{store['topic']}'. "
            "Return YAML with key 'sections', a list of up to 3 short titles. ONLY YAML."
        )
        store["outline"] = (yaml.safe_load(_strip_fence(raw)) or {}).get("sections", [])[:3]
        _publish(store, "outline", "done", outline=store["outline"])

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["draft"],)


class DraftAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        _publish(store, "draft")
        chunks = []
        for title in store["outline"]:
            chunks.append(f"## {title}\n\n" + call_llm(
                f"Write ~100 words for the section '{title}' of an article on "
                f"'{store['topic']}'. Plain prose."
            ))
        store["draft"] = "\n\n".join(chunks)
        _publish(store, "draft", "done")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["style"],)


class StyleAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        _publish(store, "style")
        store["styled"] = call_llm(
            "Rewrite the article in a friendly conversational tone. Keep section headings.\n\n"
            + store["draft"]
        )
        _publish(store, "style", "done", article=store["styled"])


def build_writing_flow() -> BaseFlow:
    o = OutlineAgent(meta=BaseMeta(name="outline"))
    d = DraftAgent(meta=BaseMeta(name="draft"))
    s = StyleAgent(meta=BaseMeta(name="style"))
    o >> d
    d >> s
    return BaseFlow(meta=BaseMeta(name="writing_flow"), branches=(o,))
