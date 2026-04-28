from collections import deque

from flow import build_lead_flow


def main() -> None:
    store: dict = {}
    deque(build_lead_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
