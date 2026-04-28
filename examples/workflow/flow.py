"""Three-stage article writing workflow.

  OutlineAgent  (3 sections in YAML)
       |
       v
  DraftAgent    (~100 words per section)
       |
       v
  StyleAgent    (rewrite in conversational tone)

A textbook linear pipeline. Each stage reads what the previous one
wrote into `store` and adds its own contribution.
"""

from typing import Any, List, Optional, Tuple

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


class OutlineAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        raw = call_llm(
            f"Create an outline for an article on '{store['topic']}'. "
            "Return YAML with key 'sections', a list of up to 3 short section titles. "
            "Output ONLY YAML, no fencing."
        )
        parsed = yaml.safe_load(_strip_fence(raw))
        store["outline"] = parsed["sections"][:3]

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["draft"],)


class DraftAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        sections: List[str] = []
        for title in store["outline"]:
            body = call_llm(
                f"Write about 100 words for the section titled '{title}' "
                f"of an article on '{store['topic']}'. Plain prose only."
            )
            sections.append(f"## {title}\n\n{body}")
        store["draft"] = "\n\n".join(sections)

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["style"],)


class StyleAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["styled"] = call_llm(
            "Rewrite the following article in a friendly, conversational, "
            "engaging tone. Keep section headings.\n\n" + store["draft"]
        )


def build_writing_flow() -> BaseFlow:
    outline = OutlineAgent(meta=BaseMeta(name="outline"))
    draft = DraftAgent(meta=BaseMeta(name="draft"))
    style = StyleAgent(meta=BaseMeta(name="style"))
    outline >> draft
    draft >> style
    return BaseFlow(meta=BaseMeta(name="writing_flow"), branches=(outline,))
