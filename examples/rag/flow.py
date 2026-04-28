"""Two-phase RAG: build an index, then answer queries against it.

Index phase (one Flow):
  ChunkAgent -> EmbedAgent

Query phase (another Flow that reuses the index):
  EmbedQueryAgent -> RetrieveAgent -> GenerateAgent
"""

from typing import Any, List, Optional, Tuple

import faiss
import numpy as np
from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat, embed


EMBED_DIM = 1536


def _split(text: str, size: int = 200) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


# ---------- Index phase ----------

class ChunkAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        chunks: List[str] = []
        for doc in store["docs"]:
            chunks.extend(_split(doc, store.get("chunk_size", 60)))
        store["chunks"] = chunks

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["embed_idx"],)


class EmbedIndexAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        idx = faiss.IndexFlatL2(EMBED_DIM)
        vecs = np.stack([embed(c) for c in store["chunks"]])
        idx.add(vecs)
        store["index"] = idx


def build_index_flow() -> BaseFlow:
    chunk = ChunkAgent(meta=BaseMeta(name="chunk"))
    eidx = EmbedIndexAgent(meta=BaseMeta(name="embed_idx"))
    chunk >> eidx
    return BaseFlow(meta=BaseMeta(name="index_flow"), branches=(chunk,))


# ---------- Query phase ----------

class EmbedQueryAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["q_vec"] = embed(store["query"]).reshape(1, -1)

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["retrieve"],)


class RetrieveAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        k = store.get("k", 3)
        _, idx = store["index"].search(store["q_vec"], k)
        store["context"] = [store["chunks"][i] for i in idx[0] if i != -1]

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["generate"],)


class GenerateAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        ctx = "\n\n".join(f"- {c}" for c in store["context"])
        store["answer"] = chat([
            {"role": "system", "content": "Answer ONLY from the context. Cite snippet numbers."},
            {"role": "user", "content": f"Context:\n{ctx}\n\nQuestion: {store['query']}"},
        ])


def build_query_flow() -> BaseFlow:
    eq = EmbedQueryAgent(meta=BaseMeta(name="embed_q"))
    retr = RetrieveAgent(meta=BaseMeta(name="retrieve"))
    gen = GenerateAgent(meta=BaseMeta(name="generate"))
    eq >> retr
    retr >> gen
    return BaseFlow(meta=BaseMeta(name="query_flow"), branches=(eq,))
