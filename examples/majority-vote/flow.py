"""Scatter K solvers, then reduce by majority vote.

Layer 0: K SolverAgents in parallel.
Closing rite of the Flow hands off to the TallyAgent — the tally lives
in `Flow.handoff`, which is the canonical place for "synthesize then
decide what's next."
"""

import re
from collections import Counter
from typing import Any, Optional, Tuple

from branchlayerflow import (
    AsyncBaseAgent,
    AsyncBaseFlow,
    AsyncParallelBaseFlow,
    BaseMeta,
)

from utils import call_llm


ANSWER_RE = re.compile(r"final answer\s*[:=]?\s*([0-9./%]+)", re.IGNORECASE)


class SolverAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        reply = await call_llm(
            f"Solve this problem step by step, then end with a line of the form "
            f"`Final answer: <number>`.\n\n{store['problem']}"
        )
        match = ANSWER_RE.search(reply)
        answer = match.group(1).strip(". ") if match else "?"
        store.setdefault("answers", []).append(answer)
        print(f"  voter {self.meta.voter_id} -> {answer}")


class TallyAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        counts = Counter(store["answers"])
        winner, votes = counts.most_common(1)[0]
        store["majority"] = {"answer": winner, "votes": votes, "tally": dict(counts)}
        print(f"\nMajority: {winner!r} with {votes}/{sum(counts.values())} votes")
        print(f"Full tally: {dict(counts)}")


class MajorityVoteFlow(AsyncParallelBaseFlow):
    """Closing rite hands off to the tally."""

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["tally"],)


def build_vote_flow(k: int = 5) -> AsyncBaseFlow:
    voters = tuple(
        SolverAgent(meta=BaseMeta(name=f"solver_{i}", voter_id=i))
        for i in range(k)
    )
    inner = MajorityVoteFlow(meta=BaseMeta(name="vote_inner"), branches=voters)
    inner >> TallyAgent(meta=BaseMeta(name="tally"))
    # Wrap so the inner flow's closing-rite handoff bubbles into a real
    # next-layer scheduling step (the tally agent).
    return AsyncBaseFlow(meta=BaseMeta(name="vote_outer"), branches=(inner,))
