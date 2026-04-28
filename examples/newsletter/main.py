from collections import deque

from flow import build_newsletter_flow


def main() -> None:
    store = {
        "topics": ["AI agents", "LLM benchmarks", "AI funding"],
        "raw": [],
        "picked": [],
        "markdown": "",
    }
    deque(build_newsletter_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
