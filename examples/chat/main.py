from collections import deque

from flow import build_chat_flow


def main() -> None:
    print("Chat (type 'exit' to quit):\n")
    deque(build_chat_flow()(store={}), maxlen=0)


if __name__ == "__main__":
    main()
