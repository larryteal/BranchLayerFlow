import asyncio
import sys

from flow import build_auto_researcher_flow


async def main() -> None:
    topic = " ".join(sys.argv[1:]) or "Where is open-source RAG (retrieval-augmented generation) heading in 2025?"
    store = {
        "topic": topic,
        "phases": 4,
        "max_verify_rounds": 2,  # 1 = no drilldown; 2 = up to one drilldown round
    }
    async for _ in build_auto_researcher_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
