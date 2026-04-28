from collections import deque

from flow import build_guardrail_flow


def main() -> None:
    print("Travel advisor (with topic guardrail). Type 'exit' to quit.\n")
    deque(build_guardrail_flow()(store={}), maxlen=0)


if __name__ == "__main__":
    main()
