"""Chat with hybrid memory.

Four agents per turn:

  GetUserAgent      (read input)
        |
        v
  RetrieveAgent     (vector-search older pairs from FAISS)
        |
        v
  AnswerAgent       (LLM call with short-term + recalled context)
        |
        +---[window full?]---> EmbedAgent (archive oldest pair to FAISS) --> GetUserAgent
        |
        +---[no]---------------> GetUserAgent

Short-term: last `WINDOW_SIZE` (q,a) pairs in `store["recent"]`.
Long-term: a FAISS L2 index plus parallel `store["archive"]` list.
"""

from typing import Any, Optional, Tuple

import faiss
import numpy as np
from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat_completion, embed


WINDOW_SIZE = 3
EMBED_DIM = 1536  # text-embedding-3-small


def _new_store() -> dict:
    return {
        "recent": [],            # list[(user, assistant)] sliding window
        "archive": [],           # list[(user, assistant)] long-term
        "index": faiss.IndexFlatL2(EMBED_DIM),
        "pending_user": "",      # current turn's user input
        "pending_recall": None,  # retrieved (user, assistant) tuple or None
        "done": False,
    }


class GetUserAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        try:
            user = input("You: ").strip()
        except EOFError:
            user = "exit"
        if user.lower() == "exit":
            store["done"] = True
            return
        store["pending_user"] = user

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return () if store["done"] else (self.successors["retrieve"],)


class RetrieveAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["pending_recall"] = None
        if store["index"].ntotal == 0:
            return
        q_vec = embed(store["pending_user"]).reshape(1, -1)
        _, idx = store["index"].search(q_vec, 1)
        if idx[0][0] != -1:
            store["pending_recall"] = store["archive"][int(idx[0][0])]

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["answer"],)


class AnswerAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        msgs = []
        if store["pending_recall"]:
            u, a = store["pending_recall"]
            msgs.append({"role": "system", "content": f"Relevant past exchange:\nUser: {u}\nAssistant: {a}"})
        for u, a in store["recent"]:
            msgs.append({"role": "user", "content": u})
            msgs.append({"role": "assistant", "content": a})
        msgs.append({"role": "user", "content": store["pending_user"]})

        reply = chat_completion(msgs)
        print(f"Assistant: {reply}")

        store["recent"].append((store["pending_user"], reply))

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if len(store["recent"]) > WINDOW_SIZE:
            return (self.successors["embed"],)
        return (self.successors["get_user"],)


class EmbedAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        oldest = store["recent"].pop(0)
        u, _ = oldest
        store["archive"].append(oldest)
        store["index"].add(embed(u).reshape(1, -1))

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["get_user"],)


def build_chat_memory_flow() -> BaseFlow:
    g = GetUserAgent(meta=BaseMeta(name="get_user"))
    r = RetrieveAgent(meta=BaseMeta(name="retrieve"))
    a = AnswerAgent(meta=BaseMeta(name="answer"))
    e = EmbedAgent(meta=BaseMeta(name="embed"))
    g >> r
    r >> a
    a >> e
    a >> g
    e >> g
    return BaseFlow(meta=BaseMeta(name="chat_mem_flow"), branches=(g,))


__all__ = ["build_chat_memory_flow", "_new_store"]
