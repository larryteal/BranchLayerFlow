import asyncio
import sys

from flow import build_deep_research_flow


async def main() -> None:
    topic = " ".join(sys.argv[1:]) or "What are the most credible recent benchmarks for agentic coding tools in 2025?"
    store = {
        "topic": topic,
        "breadth": 3,
        "max_rounds": 2,
        "evidence": [],
        "gaps": [],
    }
    async for _ in build_deep_research_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
