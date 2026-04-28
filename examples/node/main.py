from collections import deque

from flow import build_summarize_flow


SAMPLE_TEXT = (
    "BranchLayerFlow is a deliberately minimal kernel for multi-AI-agent "
    "systems. It does not bundle LLM clients, prompt libraries, tool "
    "registries, or memory abstractions — those remain yours to choose. "
    "What it gives you is the collaboration protocol that lets specialized "
    "agents take turns on a complex task, hand work off to whoever is best "
    "suited next, and synchronize teams when needed."
)


def main() -> None:
    store = {"data": SAMPLE_TEXT, "summary": None}
    flow = build_summarize_flow()
    deque(flow(store=store), maxlen=0)
    print(f"Summary: {store['summary']}")


if __name__ == "__main__":
    main()
