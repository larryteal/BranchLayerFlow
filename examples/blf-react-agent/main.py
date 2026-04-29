import asyncio
import sys

from flow import build_react_agent_flow


async def main() -> None:
    goal = " ".join(sys.argv[1:]) or "What is the latest reported context-window size of GPT-5, with a primary source?"
    store = {"goal": goal, "max_steps": 6}
    async for _ in build_react_agent_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
