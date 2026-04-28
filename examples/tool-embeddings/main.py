from collections import deque

from flow import build_embed_flow


def main() -> None:
    store = {
        "texts": [
            "BLF is a minimal multi-agent kernel.",
            "Coffee tastes better in the morning.",
            "Layered barriers structure agent communication.",
            "I prefer espresso over filter coffee.",
        ],
    }
    deque(build_embed_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
