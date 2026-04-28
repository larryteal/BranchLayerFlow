from collections import deque

from flow import build_mermaid_flow


def main() -> None:
    store = {
        "description": (
            "A 5-state finite-state machine for an order: NEW -> PAID -> SHIPPED -> "
            "DELIVERED, with a CANCELLED state reachable from NEW or PAID."
        ),
    }
    deque(build_mermaid_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
