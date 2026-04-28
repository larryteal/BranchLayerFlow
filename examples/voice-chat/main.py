from collections import deque

from flow import build_voice_flow


def main() -> None:
    print("Voice chat (say 'exit' to quit).")
    deque(build_voice_flow()(store={}), maxlen=0)


if __name__ == "__main__":
    main()
