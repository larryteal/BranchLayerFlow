"""Per-pair sub-flow, all assembled as branches of one outer flow.

Each (image, filter) pair gets its own three-agent sub-flow:
  Load -> Apply -> Save
Because **Flow IS Agent**, those sub-flows can be branches of an outer
Flow — no special "batch flow" type is needed.
"""

from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta
from PIL import Image, ImageFilter, ImageOps


FILTERS = {
    "grayscale": lambda img: ImageOps.grayscale(img).convert("RGB"),
    "blur": lambda img: img.filter(ImageFilter.GaussianBlur(radius=4)),
    "sepia": lambda img: _sepia(img),
}


def _sepia(img: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(img)
    return ImageOps.colorize(gray, black=(60, 30, 0), white=(255, 220, 180))


class LoadAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["image"] = Image.open(store["src_path"]).convert("RGB")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["apply"],)


class ApplyAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        fn = FILTERS[store["filter_name"]]
        store["image"] = fn(store["image"])

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["save"],)


class SaveAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["image"].save(store["dst_path"], "PNG")
        print(f"  saved {Path(store['dst_path']).name}")


def build_one_image_flow(name: str) -> BaseFlow:
    load = LoadAgent(meta=BaseMeta(name="load"))
    apply_ = ApplyAgent(meta=BaseMeta(name="apply"))
    save = SaveAgent(meta=BaseMeta(name="save"))
    load >> apply_
    apply_ >> save
    return BaseFlow(meta=BaseMeta(name=name), branches=(load,))


class DispatcherAgent(BaseAgent):
    """Builds and hands off one sub-flow per (image, filter) pair.

    The handoff returns a tuple of Flows — each Flow IS an Agent, so
    BLF schedules them as next-layer peers exactly like single agents.
    The Flow's per-run private store is built here too.
    """

    def takeover(self, store: Any) -> None:
        store["sub_stores"] = []

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        out_dir = Path(store["out_dir"])
        flows = []
        for img_path in store["image_paths"]:
            for filter_name in store["filters"]:
                stem = Path(img_path).stem
                dst = out_dir / f"{stem}_{filter_name}.png"
                sub_store = {
                    "src_path": img_path,
                    "dst_path": str(dst),
                    "filter_name": filter_name,
                }
                store["sub_stores"].append(sub_store)
                sub_flow = build_one_image_flow(f"sub_{stem}_{filter_name}")
                # Each sub-flow runs against its own store via a closure agent
                flows.append(_BoundFlow(sub_flow, sub_store))
        return tuple(flows)


class _BoundFlow(BaseAgent):
    """Tiny wrapper: drives a sub-flow against an isolated per-pair store."""

    def __init__(self, flow: BaseFlow, sub_store: Any) -> None:
        super().__init__(meta=BaseMeta(name=f"bound_{flow.meta.name}"))
        self._flow = flow
        self._sub_store = sub_store

    def takeover(self, store: Any) -> None:
        from collections import deque
        deque(self._flow(store=self._sub_store), maxlen=0)


def build_batch_flow() -> BaseFlow:
    dispatcher = DispatcherAgent(meta=BaseMeta(name="dispatcher"))
    return BaseFlow(meta=BaseMeta(name="batch_flow"), branches=(dispatcher,))
