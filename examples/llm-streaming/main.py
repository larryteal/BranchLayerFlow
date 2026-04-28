from collections import deque

from flow import build_stream_flow


def main() -> None:
    print("Streaming demo (press ENTER to interrupt). Set USE_REAL_LLM=1 for the real API.\n")
    store = {"prompt": "Explain backpropagation in 5 steps.", "response": ""}
    deque(build_stream_flow()(store=store), maxlen=0)
    print(f"\nAccumulated {len(store['response'])} chars.")


if __name__ == "__main__":
    main()
