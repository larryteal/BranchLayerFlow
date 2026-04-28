"""Split-process-combine inside one agent.

A "batch node" is split (prep) -> exec per chunk -> combine (post).
In BLF the same shape is just three private methods called from
`takeover` — no batch primitive needed.
"""

import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta


class CSVAggregateAgent(BaseAgent):
    """Reads a CSV in chunks, accumulates totals per chunk, combines at the end."""

    def takeover(self, store: Any) -> None:
        chunks = list(self._split(store["csv_path"], store["chunk_size"]))
        partials = [self._process(chunk) for chunk in chunks]
        store["stats"] = self._combine(partials)

    def _split(self, path: str, chunk_size: int) -> Iterable[List[Dict[str, str]]]:
        with open(path, newline="") as fh:
            reader = csv.DictReader(fh)
            buf: List[Dict[str, str]] = []
            for row in reader:
                buf.append(row)
                if len(buf) == chunk_size:
                    yield buf
                    buf = []
            if buf:
                yield buf

    def _process(self, chunk: List[Dict[str, str]]) -> Dict[str, float]:
        total = sum(float(r["amount"]) for r in chunk)
        return {"sum": total, "count": float(len(chunk))}

    def _combine(self, partials: List[Dict[str, float]]) -> Dict[str, float]:
        total = sum(p["sum"] for p in partials)
        count = sum(p["count"] for p in partials)
        return {
            "total_sales": total,
            "transaction_count": int(count),
            "average_transaction": total / count if count else 0.0,
        }


def build_aggregate_flow() -> BaseFlow:
    agent = CSVAggregateAgent(meta=BaseMeta(name="csv_aggregate"))
    return BaseFlow(meta=BaseMeta(name="aggregate_flow"), branches=(agent,))
