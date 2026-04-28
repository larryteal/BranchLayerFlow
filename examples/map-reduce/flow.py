"""Map-reduce over a directory of resumes.

Map  layer: one EvaluateAgent per resume, all running in parallel.
Reduce step: in `Flow.handoff` — the canonical synthesize-then-route place.
"""

import re
from pathlib import Path
from typing import Any, Optional, Tuple

import yaml
from branchlayerflow import (
    AsyncBaseAgent,
    AsyncParallelBaseFlow,
    BaseMeta,
)

from utils import call_llm


def _strip_fence(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            body = parts[1]
            if body.startswith("yaml"):
                body = body[4:]
            return body
    return text


class EvaluateAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        path = Path(self.meta.resume_path)
        text = path.read_text(encoding="utf-8")
        raw = await call_llm(
            "Evaluate the following resume for a senior backend engineer role. "
            "Return ONLY YAML with two keys: `qualified` (true/false) and "
            "`reason` (one sentence).\n\n"
            f"RESUME ({path.name}):\n{text}"
        )
        try:
            verdict = yaml.safe_load(_strip_fence(raw)) or {}
        except yaml.YAMLError:
            verdict = {"qualified": False, "reason": "parse error"}
        store.setdefault("verdicts", {})[path.name] = {
            "qualified": bool(verdict.get("qualified", False)),
            "reason": verdict.get("reason", ""),
        }


class MapReduceFlow(AsyncParallelBaseFlow):
    """Reduce step lives in the closing rite."""

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        verdicts = store.get("verdicts", {})
        qualified = [n for n, v in verdicts.items() if v["qualified"]]
        store["summary"] = {
            "total": len(verdicts),
            "qualified": len(qualified),
            "qualified_names": qualified,
            "rate": len(qualified) / len(verdicts) if verdicts else 0.0,
        }
        s = store["summary"]
        print(f"\n{s['qualified']}/{s['total']} qualified ({s['rate']:.0%})")
        for name in qualified:
            print(f"  PASS  {name} — {verdicts[name]['reason']}")
        for name, v in verdicts.items():
            if not v["qualified"]:
                print(f"  FAIL  {name} — {v['reason']}")
        return None


def build_map_reduce_flow(resume_dir: Path) -> MapReduceFlow:
    branches = tuple(
        EvaluateAgent(meta=BaseMeta(
            name=f"evaluate_{p.stem}",
            resume_path=str(p),
        ))
        for p in sorted(resume_dir.glob("*.txt"))
    )
    return MapReduceFlow(meta=BaseMeta(name="map_reduce"), branches=branches)
