from collections import deque

from flow import build_heartbeat_flow


def main() -> None:
    store = {"interval": 1.0, "max_cycles": 3}
    deque(build_heartbeat_flow()(store=store), maxlen=0)
    print(f"\nProcessed total: {len(store.get('processed', []))} messages")


if __name__ == "__main__":
    main()
