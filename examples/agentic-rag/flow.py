"""Agentic RAG: the agent picks which document to read next.

  DecideAgent  -- read summaries + already-read docs; emit either
                  `READ: <doc_id>` or `ANSWER`.
        |
        +--[read]----> ReadDocAgent --> DecideAgent (loop)
        +--[answer]--> AnswerAgent --> ()
"""

import re
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat


READ_RE = re.compile(r"READ:\s*([^\s]+)", re.IGNORECASE)


def _summary_block(store: Any) -> str:
    return "\n".join(f"- {d['id']}: {d['summary']}" for d in store["library"])


class DecideAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        already = ", ".join(store["read_ids"]) or "(none)"
        decision = chat([
            {"role": "system", "content": (
                "You are an agentic RAG controller. Look at document SUMMARIES "
                "and already-read full docs, and choose the next action. Reply "
                "with EXACTLY one of:\n"
                "  READ: <doc_id>   (open one more doc)\n"
                "  ANSWER           (you have enough; commit an answer)"
            )},
            {"role": "user", "content": (
                f"Question: {store['query']}\n\n"
                f"Available summaries:\n{_summary_block(store)}\n\n"
                f"Already read: {already}\n\n"
                f"Excerpts in hand:\n" + ("\n---\n".join(store['read_bodies']) or "(none)")
            )},
        ]).strip()
        store["decision"] = decision

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        m = READ_RE.search(store["decision"])
        if m and len(store["read_ids"]) < self.meta.max_reads:
            doc_id = m.group(1).strip(".,")
            if doc_id not in store["read_ids"]:
                store["pending_doc"] = doc_id
                return (self.successors["read"],)
        return (self.successors["answer"],)


class ReadDocAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        doc_id = store["pending_doc"]
        doc = next((d for d in store["library"] if d["id"] == doc_id), None)
        if doc:
            store["read_ids"].append(doc_id)
            store["read_bodies"].append(f"{doc_id}: {doc['body']}")
            print(f"[read] {doc_id}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["decide"],)


class AnswerAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["answer"] = chat([
            {"role": "system", "content": "Answer the question using only the excerpts."},
            {"role": "user", "content": (
                f"Question: {store['query']}\n\n"
                f"Excerpts:\n" + "\n---\n".join(store['read_bodies'])
            )},
        ])
        print(f"\n=== Answer ===\n{store['answer']}")


def build_agentic_rag_flow() -> BaseFlow:
    decide = DecideAgent(meta=BaseMeta(name="decide", max_reads=3))
    read = ReadDocAgent(meta=BaseMeta(name="read"))
    ans = AnswerAgent(meta=BaseMeta(name="answer"))
    decide >> read
    decide >> ans
    read >> decide
    return BaseFlow(meta=BaseMeta(name="agentic_rag"), branches=(decide,))
