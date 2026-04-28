from collections import deque

from flow import build_search_flow


def main() -> None:
    store = {"query": "BSP model in distributed systems", "num": 5, "results": [], "analysis": ""}
    deque(build_search_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
