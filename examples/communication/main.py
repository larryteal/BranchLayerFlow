from collections import deque

from flow import build_stats_flow


def main() -> None:
    store: dict = {}
    deque(build_stats_flow()(store=store), maxlen=0)
    print("Goodbye.")


if __name__ == "__main__":
    main()
