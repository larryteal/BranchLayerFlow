from collections import deque

from flow import build_agentic_rag_flow


LIBRARY = [
    {
        "id": "doc-bsp",
        "summary": "BSP / Pregel — superstep model, cross-superstep barriers.",
        "body": "Bulk Synchronous Parallel divides work into supersteps. Vertices "
                "process in parallel within a superstep and communicate only across "
                "barriers between supersteps.",
    },
    {
        "id": "doc-actor",
        "summary": "Actor model — message passing, no shared memory.",
        "body": "Actors are isolated computational units that communicate by sending "
                "messages. There is no shared mutable state; each actor processes its "
                "own mailbox.",
    },
    {
        "id": "doc-blf",
        "summary": "BLF — minimal multi-agent kernel; takeover/handoff; layer barriers.",
        "body": "BranchLayerFlow exposes only takeover and handoff. Same-layer agents "
                "do not see each other directly; they communicate through the shared "
                "store between layers, which mirrors BSP's superstep barrier discipline.",
    },
    {
        "id": "doc-csp",
        "summary": "CSP — synchronous channel rendezvous.",
        "body": "Communicating Sequential Processes use synchronous channels: a sender "
                "blocks until a receiver is ready and vice versa.",
    },
]


def main() -> None:
    store = {
        "query": "How does BLF's concurrency model relate to BSP?",
        "library": LIBRARY,
        "read_ids": [],
        "read_bodies": [],
        "answer": "",
    }
    deque(build_agentic_rag_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
