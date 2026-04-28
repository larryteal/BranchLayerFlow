import asyncio

from flow import build_vote_flow


PROBLEM = (
    "A factory keeps shoes in pairs. From a bin of 10 pairs, you draw 6 "
    "individual shoes uniformly at random without replacement. What is the "
    "probability that the 6 shoes form exactly 3 matched pairs? Express the "
    "result as a decimal rounded to 4 places."
)


async def main() -> None:
    store = {"problem": PROBLEM, "answers": []}
    flow = build_vote_flow(k=5)
    async for _ in flow(store=store):
        pass


if __name__ == "__main__":
    asyncio.run(main())
