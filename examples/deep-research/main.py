import asyncio

from flow import build_deep_research_flow


async def main() -> None:
    store = {
        "topic": "How does the BSP (Bulk Synchronous Parallel) model influence "
                 "the design of multi-agent LLM systems?",
        "max_rounds": 2,
        "facts": [],
        "raw_snippets": [],
        "gaps": [],
        "round": 0,
    }
    async for _ in build_deep_research_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
