from collections import deque
from pathlib import Path

from flow import build_skills_flow


def main() -> None:
    here = Path(__file__).parent
    store = {
        "skills_dir": str(here / "skills"),
        "request": (
            "Please summarize the following meeting notes for an executive: "
            "We discussed Q2 revenue, agreed on hiring two engineers, and "
            "decided to delay the EMEA launch by one quarter due to compliance."
        ),
    }
    deque(build_skills_flow()(store=store), maxlen=0)
    print(f"\n--- Output ---\n{store['output']}")


if __name__ == "__main__":
    main()
