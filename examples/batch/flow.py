"""Sequential batch translation.

A single TranslateBatchAgent loops through every target language inside
its own `takeover`, calling the LLM serially.

In BLF, "batch as one Node" is just a Python loop inside one agent. The
framework provides no built-in batch primitive because none is needed —
the loop primitive is `for`.

For the parallel variant, see `examples/parallel-batch`.
"""

from pathlib import Path
from typing import Any

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


LANGUAGES = [
    "Chinese", "Spanish", "Japanese", "German",
    "Russian", "Portuguese", "French", "Korean",
]


class TranslateBatchAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        out_dir = Path(store["out_dir"])
        for language in LANGUAGES:
            print(f"  translating to {language}...")
            translated = call_llm(
                f"Translate the following markdown document to {language}. "
                "Preserve all markdown formatting, links, code blocks, and "
                "image references. Do not translate code or URLs.\n\n"
                f"{store['source']}"
            )
            path = out_dir / f"README_{language.upper()}.md"
            path.write_text(translated, encoding="utf-8")
            store["written"].append(str(path))


def build_translate_flow() -> BaseFlow:
    agent = TranslateBatchAgent(meta=BaseMeta(name="translate_batch"))
    return BaseFlow(meta=BaseMeta(name="batch_translate_flow"), branches=(agent,))
