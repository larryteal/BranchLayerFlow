"""Skill selector + skill executor.

  SelectAgent   -- read user request + skill index, emit `SKILL: <name>`
        |
        v
  ApplyAgent    -- load that skill's markdown, use it as system prompt
"""

import re
from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat


SKILL_RE = re.compile(r"SKILL:\s*([\w_-]+)", re.IGNORECASE)


def _skill_index(skills_dir: Path) -> str:
    lines = []
    for p in sorted(skills_dir.glob("*.md")):
        first = p.read_text(encoding="utf-8").strip().splitlines()[0]
        lines.append(f"- {p.stem}: {first[:120]}")
    return "\n".join(lines)


class SelectAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        skills_dir = Path(store["skills_dir"])
        index = _skill_index(skills_dir)
        decision = chat([
            {"role": "system", "content": (
                "Pick the single skill that best fits the user's request. "
                "Reply with EXACTLY `SKILL: <name>` and nothing else, where "
                "<name> is one of the listed skill ids."
            )},
            {"role": "user", "content": (
                f"Available skills:\n{index}\n\nRequest:\n{store['request']}"
            )},
        ])
        m = SKILL_RE.search(decision)
        store["chosen_skill"] = m.group(1).strip() if m else None
        print(f"[selector] -> {store['chosen_skill']!r}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["apply"],)


class ApplyAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        chosen = store.get("chosen_skill")
        if not chosen:
            store["output"] = "(no skill selected)"
            return
        path = Path(store["skills_dir"]) / f"{chosen}.md"
        if not path.exists():
            store["output"] = f"(unknown skill: {chosen})"
            return
        skill_prompt = path.read_text(encoding="utf-8")
        store["output"] = chat([
            {"role": "system", "content": skill_prompt},
            {"role": "user", "content": store["request"]},
        ])


def build_skills_flow() -> BaseFlow:
    sel = SelectAgent(meta=BaseMeta(name="select"))
    ap = ApplyAgent(meta=BaseMeta(name="apply"))
    sel >> ap
    return BaseFlow(meta=BaseMeta(name="skills_flow"), branches=(sel,))
