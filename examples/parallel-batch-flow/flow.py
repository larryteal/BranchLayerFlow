"""Parallel image processing using AsyncParallelBaseFlow.

Same structure as `batch-flow` but every sub-flow runs concurrently:
the outer Flow uses `AsyncParallelBaseFlow` so all (image, filter) pairs
process their three-step pipeline in parallel.
"""

import asyncio
from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import (
    AsyncBaseAgent,
    AsyncBaseFlow,
    AsyncParallelBaseFlow,
    BaseMeta,
)
from PIL import Image, ImageFilter, ImageOps


FILTERS = {
    "grayscale": lambda img: ImageOps.grayscale(img).convert("RGB"),
    "blur": lambda img: img.filter(ImageFilter.GaussianBlur(radius=4)),
    "sepia": lambda img: _sepia(img),
}


def _sepia(img: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(img)
    return ImageOps.colorize(gray, black=(60, 30, 0), white=(255, 220, 180))


class LoadAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        loop = asyncio.get_event_loop()
        store["image"] = await loop.run_in_executor(
            None, lambda: Image.open(store["src_path"]).convert("RGB")
        )

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["apply"],)


class ApplyAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        loop = asyncio.get_event_loop()
        store["image"] = await loop.run_in_executor(
            None, FILTERS[store["filter_name"]], store["image"]
        )

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["save"],)


class SaveAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: store["image"].save(store["dst_path"], "PNG")
        )
        print(f"  saved {Path(store['dst_path']).name}")


def build_one_pair_flow(name: str) -> AsyncBaseFlow:
    load = LoadAgent(meta=BaseMeta(name="load"))
    apply_ = ApplyAgent(meta=BaseMeta(name="apply"))
    save = SaveAgent(meta=BaseMeta(name="save"))
    load >> apply_
    apply_ >> save
    return AsyncBaseFlow(meta=BaseMeta(name=name), branches=(load,))


class _BoundFlow(AsyncBaseAgent):
    """Drives a per-pair sub-flow against an isolated store."""

    def __init__(self, flow: AsyncBaseFlow, sub_store: Any) -> None:
        super().__init__(meta=BaseMeta(name=f"bound_{flow.meta.name}"))
        self._flow = flow
        self._sub_store = sub_store

    async def takeover(self, store: Any) -> None:
        async for _ in self._flow(store=self._sub_store):
            pass


def build_parallel_batch_flow(image_paths, filters, out_dir) -> AsyncParallelBaseFlow:
    out_dir = Path(out_dir)
    branches = []
    for img_path in image_paths:
        for filter_name in filters:
            stem = Path(img_path).stem
            sub_store = {
                "src_path": img_path,
                "dst_path": str(out_dir / f"{stem}_{filter_name}.png"),
                "filter_name": filter_name,
            }
            sub = build_one_pair_flow(f"sub_{stem}_{filter_name}")
            branches.append(_BoundFlow(sub, sub_store))
    return AsyncParallelBaseFlow(
        meta=BaseMeta(name="parallel_batch_flow"),
        branches=tuple(branches),
    )
