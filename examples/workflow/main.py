from collections import deque

from flow import build_writing_flow


def main() -> None:
    store = {"topic": "The future of multi-agent systems", "outline": [], "draft": "", "styled": ""}
    deque(build_writing_flow()(store=store), maxlen=0)
    print(f"Outline: {store['outline']}\n")
    print(f"=== Final article ===\n{store['styled']}")


if __name__ == "__main__":
    main()
