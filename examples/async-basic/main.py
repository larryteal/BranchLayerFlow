import asyncio

from flow import build_recipe_flow


async def main() -> None:
    store = {"ingredient": "", "recipes": [], "suggestion": "", "accepted": False}
    async for _ in build_recipe_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
