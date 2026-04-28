"""PDF OCR pipeline using GPT-4o vision.

  RasterAgent    (PDF -> list of PIL images)
       |
       v
  ExtractAgent   (one vision call per page; concatenates the text)
"""

from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from tool_pdf import pdf_to_images, vision_extract


class RasterAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["pages"] = pdf_to_images(Path(store["pdf_path"]))
        print(f"rendered {len(store['pages'])} pages")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["extract"],)


class ExtractAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        instruction = store.get("instruction", "Extract all text verbatim.")
        out = []
        for i, img in enumerate(store["pages"], 1):
            print(f"  vision page {i}/{len(store['pages'])}")
            out.append(f"--- page {i} ---\n{vision_extract(img, instruction)}")
        store["text"] = "\n\n".join(out)


def build_pdf_flow() -> BaseFlow:
    raster = RasterAgent(meta=BaseMeta(name="raster"))
    extract = ExtractAgent(meta=BaseMeta(name="extract"))
    raster >> extract
    return BaseFlow(meta=BaseMeta(name="pdf_flow"), branches=(raster,))
