from collections import deque

from flow import build_debate_flow


def main() -> None:
    store = {"claim": "Multi-agent systems should externalize routing decisions to the agents themselves."}
    deque(build_debate_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
