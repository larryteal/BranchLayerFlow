import asyncio
import sys

from flow import build_wide_research_flow


async def main() -> None:
    topic = " ".join(sys.argv[1:]) or "What is the current state of small language models in 2025?"
    store = {"topic": topic, "breadth": 5}
    async for _ in build_wide_research_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
