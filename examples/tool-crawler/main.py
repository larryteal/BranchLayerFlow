import asyncio
import os

from flow import build_crawl_flow


async def main() -> None:
    store = {
        "seed": os.environ.get("CRAWL_SEED", "https://example.com/"),
        "max_pages": 3,
        "pages": [],
        "analyses": [],
    }
    async for _ in build_crawl_flow()(store=store):
        pass
    print("\n--- Analyses ---")
    for a in store["analyses"]:
        print(f"\n{a['url']}\n{a['analysis']}")


if __name__ == "__main__":
    asyncio.run(main())
