"""Entry point for the autoresearch report hill-climber.

Reads the topic from CLI argv, the loop knobs from env (with sane defaults),
and runs the flow to completion.
"""

import argparse
import asyncio
import os

from flow import build_autoresearch_flow


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def _env_float(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Autoresearch hill-climber on a research report.",
    )
    p.add_argument("topic", nargs="*", help="Research topic (positional). May span multiple words.")
    p.add_argument("--budget",  type=int,   default=_env_int("BUDGET", 8),
                   help="Max rounds (default 8 or $BUDGET).")
    p.add_argument("--beam",    type=int,   default=_env_int("BEAM", 3),
                   help="Parallel proposers per round (default 3 or $BEAM).")
    p.add_argument("--target",  type=float, default=_env_float("TARGET_SCORE", 90.0),
                   help="Stop when best score >= this (default 90 or $TARGET_SCORE).")
    p.add_argument("--patience", type=int,  default=_env_int("PATIENCE", 3),
                   help="Stop after this many no-improvement rounds (default 3 or $PATIENCE).")
    p.add_argument("--out", default=os.environ.get("OUT_DIR", "output"),
                   help="Output directory (default ./output or $OUT_DIR).")
    return p.parse_args()


async def main() -> None:
    args = parse_args()
    topic = " ".join(args.topic) or "What are the production limits of agentic browsers in 2026?"
    store = {
        "topic": topic,
        "budget": args.budget,
        "beam": args.beam,
        "target_score": args.target,
        "patience": args.patience,
        "out_dir": args.out,
    }
    async for _ in build_autoresearch_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
