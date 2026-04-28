from collections import deque
from pathlib import Path

from flow import build_db_flow


def main() -> None:
    db = Path(__file__).parent / "tasks.sqlite"
    if db.exists():
        db.unlink()
    store = {
        "db_path": str(db),
        "initial": [
            "design layered concurrency model",
            "write hello-world example",
            "publish v0.1 to PyPI",
            "open repo for community examples",
        ],
        "ids": [],
    }
    deque(build_db_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
