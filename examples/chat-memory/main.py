from collections import deque

from flow import build_chat_memory_flow, _new_store


def main() -> None:
    print("Chat with memory (window=3 + FAISS recall). Type 'exit' to quit.\n")
    deque(build_chat_memory_flow()(store=_new_store()), maxlen=0)


if __name__ == "__main__":
    main()
