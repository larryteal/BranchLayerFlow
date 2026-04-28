from collections import deque

from flow import build_research_flow


def main() -> None:
    store = {
        "query": "Why is BSP a good model for multi-agent collaboration?",
        "notes": [],
        "answer": "",
    }
    deque(build_research_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
