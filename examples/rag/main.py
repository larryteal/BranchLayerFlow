from collections import deque

from flow import build_index_flow, build_query_flow


DOCS = [
    "BLF (BranchLayerFlow) is a deliberately minimal multi-agent kernel. "
    "It exposes only takeover and handoff and lets you build everything else "
    "by inheritance.",
    "Layer barriers are built in: same-layer branches never see each other "
    "directly; communication happens through the shared store between layers.",
    "Flow IS Agent. A Flow can be returned from another agent's handoff "
    "exactly like a single agent — composition is free.",
    "BLF intentionally has no built-in retry, timeout, or memory. Those are "
    "user-defined subclasses, keeping the framework small and stable as the "
    "LLM ecosystem evolves.",
]


def main() -> None:
    store = {"docs": DOCS}
    deque(build_index_flow()(store=store), maxlen=0)
    print(f"Indexed {len(store['chunks'])} chunks.\n")

    store["query"] = "What does BLF say about layer barriers?"
    deque(build_query_flow()(store=store), maxlen=0)
    print(f"Q: {store['query']}\nA: {store['answer']}")


if __name__ == "__main__":
    main()
