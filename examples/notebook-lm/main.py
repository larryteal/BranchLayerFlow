from collections import deque
from pathlib import Path

from flow import build_podcast_flow


DOC = """\
# BranchLayerFlow

BLF is a deliberately minimal multi-agent orchestration kernel. It exposes
two verbs (takeover, handoff) and lets users build everything else by
inheritance.

# Layered Concurrency

Layer barriers are built in: same-layer agents do not see each other
directly. Communication happens only through the shared store between
layers, which mirrors BSP / Pregel.

# Composition

Flow IS Agent. A Flow can be returned from any handoff exactly like a
single agent, so sub-teams compose freely.
"""


def main() -> None:
    here = Path(__file__).parent
    store = {
        "document": DOC,
        "out_dir": str(here / "out"),
    }
    deque(build_podcast_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
