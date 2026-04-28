from collections import deque

from flow import build_thinking_flow


PROBLEM = (
    "Roll a fair six-sided die repeatedly. What is the probability that the "
    "first time you observe the consecutive sequence 3, 4, 5 occurs on an "
    "odd-numbered roll? Show your reasoning."
)


def main() -> None:
    store = {"problem": PROBLEM}
    deque(build_thinking_flow()(store=store), maxlen=0)
    if "final" in store:
        print(f"\n=== Final answer ===\n{store['final']}")
    else:
        print("\n(reached max steps without committing to a final answer)")


if __name__ == "__main__":
    main()
