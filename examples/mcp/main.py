import asyncio

from flow import build_mcp_flow


async def main() -> None:
    store = {"question": "What is 47 multiplied by 53?"}
    async for _ in build_mcp_flow()(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
