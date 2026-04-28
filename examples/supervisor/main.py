from collections import deque

from flow import build_supervised_flow


def main() -> None:
    store = {"query": "Why are layered barriers a useful primitive in multi-agent systems?"}
    deque(build_supervised_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
