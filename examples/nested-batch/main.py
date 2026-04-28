import random
from collections import deque
from pathlib import Path

from flow import build_school_flow


def _seed_school(root: Path) -> None:
    random.seed(0)
    if root.exists():
        return
    root.mkdir(parents=True)
    for class_id in ("a", "b"):
        class_dir = root / class_id
        class_dir.mkdir()
        for student in range(1, 4):
            grades = [random.randint(60, 100) for _ in range(5)]
            (class_dir / f"s{student}.txt").write_text("\n".join(map(str, grades)))


def main() -> None:
    here = Path(__file__).parent
    root = here / "school"
    _seed_school(root)

    store: dict = {}
    deque(build_school_flow(root)(store=store), maxlen=0)

    print("Per-student averages:")
    for sid, avg in sorted(store["students"].items()):
        print(f"  {sid}: {avg:.2f}")
    print("\nPer-class averages:")
    for cid, avg in sorted(store["class_avgs"].items()):
        print(f"  class_{cid}: {avg:.2f}")
    print(f"\nSchool average: {store['school_avg']:.2f}")


if __name__ == "__main__":
    main()
