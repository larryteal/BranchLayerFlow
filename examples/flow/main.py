from collections import deque

from flow import build_text_flow


def main() -> None:
    store = {"text": "", "choice": "", "again": False}
    deque(build_text_flow()(store=store), maxlen=0)
    print("Goodbye.")


if __name__ == "__main__":
    main()
