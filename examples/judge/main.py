from collections import deque

from flow import build_judge_flow


def main() -> None:
    store = {"product": "noise-cancelling over-ear headphones with 40h battery"}
    deque(build_judge_flow()(store=store), maxlen=0)
    print(f"\nFinal description (score={store['score']}):\n{store['candidate']}")


if __name__ == "__main__":
    main()
