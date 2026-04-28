from collections import deque

from flow import build_tao_flow


def main() -> None:
    store = {
        "problem": (
            "What is the value of (47 * 53) plus the square of 12, "
            "minus 7? Use the calculator and commit a final number."
        ),
    }
    deque(build_tao_flow()(store=store), maxlen=0)
    print(f"\nFinal answer: {store.get('final', '(none)')}")


if __name__ == "__main__":
    main()
