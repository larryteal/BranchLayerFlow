from collections import deque

from flow import build_joke_flow


def main() -> None:
    deque(build_joke_flow()(store={}), maxlen=0)
    print("Approved.")


if __name__ == "__main__":
    main()
