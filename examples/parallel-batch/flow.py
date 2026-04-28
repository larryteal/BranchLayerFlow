"""Parallel translation: 8 peer agents run inside a single layer concurrently.

`AsyncParallelBaseFlow` overrides the layer scheduler to use
`asyncio.gather`, so all branches at the same layer execute at once.
The cross-layer barrier still holds — the run finishes only when every
agent in this layer is done.
"""

from pathlib import Path
from typing import Any

from branchlayerflow import AsyncBaseAgent, AsyncParallelBaseFlow, BaseMeta

from utils import call_llm


LANGUAGES = [
    "Chinese", "Spanish", "Japanese", "German",
    "Russian", "Portuguese", "French", "Korean",
]


class TranslateAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        language = self.meta.language
        translated = await call_llm(
            f"Translate the following markdown document to {language}. "
            "Preserve all markdown formatting, links, code blocks, and "
            "image references. Do not translate code or URLs.\n\n"
            f"{store['source']}"
        )
        path = Path(store["out_dir"]) / f"README_{language.upper()}.md"
        path.write_text(translated, encoding="utf-8")
        store["written"].append(str(path))
        print(f"  done: {path.name}")


def build_parallel_translate_flow() -> AsyncParallelBaseFlow:
    branches = tuple(
        TranslateAgent(meta=BaseMeta(name=f"translate_{lang.lower()}", language=lang))
        for lang in LANGUAGES
    )
    return AsyncParallelBaseFlow(
        meta=BaseMeta(name="parallel_translate"),
        branches=branches,
    )
