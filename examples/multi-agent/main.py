import asyncio

from flow import build_taboo_flow


async def main() -> None:
    store = {
        "target": "nostalgia",
        "forbidden": ["memory", "past", "remember", "feeling", "longing", "yearning"],
        "transcript": [],
        "guess": "",
        "max_rounds": 6,
    }
    async for _ in build_taboo_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
