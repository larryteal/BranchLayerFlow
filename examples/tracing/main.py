from collections import deque

from flow import build_traced_flow
from tracer import Sink


def main() -> None:
    sink = Sink()
    store: dict = {}
    deque(build_traced_flow(sink)(store=store), maxlen=0)
    print(f"\nResult: total={store['total']}")
    print(f"Captured {len(sink.events)} trace events.")


if __name__ == "__main__":
    main()
