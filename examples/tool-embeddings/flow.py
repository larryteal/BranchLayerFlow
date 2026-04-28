"""Embed agent + similarity report."""

from typing import Any, Optional, Tuple

import numpy as np
from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from tool_embed import embed


class EmbedAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["vectors"] = embed(store["texts"])
        print(f"Embedded {len(store['texts'])} texts -> shape {store['vectors'].shape}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["report"],)


class SimilarityAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        v = store["vectors"]
        v_norm = v / np.linalg.norm(v, axis=1, keepdims=True)
        sim = v_norm @ v_norm.T
        print("\nCosine similarity matrix:")
        for i, t in enumerate(store["texts"]):
            print(f"  {i}. {t[:40]:<40} ", " ".join(f"{sim[i][j]:.2f}" for j in range(len(store["texts"]))))


def build_embed_flow() -> BaseFlow:
    e = EmbedAgent(meta=BaseMeta(name="embed"))
    r = SimilarityAgent(meta=BaseMeta(name="report"))
    e >> r
    return BaseFlow(meta=BaseMeta(name="embed_flow"), branches=(e,))
