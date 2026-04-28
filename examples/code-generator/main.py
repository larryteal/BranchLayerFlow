from collections import deque

from flow import build_codegen_flow


PROBLEM = (
    "Write a function `is_palindrome(s: str) -> bool` that returns True if `s` "
    "reads the same forwards and backwards, ignoring case and non-alphanumeric "
    "characters. Empty string should return True."
)


def main() -> None:
    store = {"problem": PROBLEM}
    deque(build_codegen_flow()(store=store), maxlen=0)
    print(f"\nPassed: {store['passed']}, attempts: {store['attempts']}")
    print(f"\n--- Final implementation ---\n{store['impl']}")


if __name__ == "__main__":
    main()
