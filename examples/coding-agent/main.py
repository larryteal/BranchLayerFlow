import sys
from collections import deque
from pathlib import Path

from flow import build_coding_agent_flow


def _seed(root: Path) -> None:
    if root.exists():
        return
    root.mkdir(parents=True)
    (root / "calc.py").write_text("def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    pass  # TODO\n")
    (root / "test_calc.py").write_text(
        "import unittest\nfrom calc import add, mul\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_add(self): self.assertEqual(add(2, 3), 5)\n"
        "    def test_mul(self): self.assertEqual(mul(3, 4), 12)\n\n"
        "if __name__ == '__main__': unittest.main()\n"
    )


def main() -> None:
    here = Path(__file__).parent
    sandbox = here / "sandbox"
    _seed(sandbox)

    store = {
        "root": str(sandbox),
        "task": (
            "Make `python -m unittest test_calc.py` pass. The `mul` function "
            "in calc.py is unimplemented; fix it."
        ),
        "history": [],
        "pending_action": None,
        "pending_result": "",
        "finished": False,
    }
    deque(build_coding_agent_flow()(store=store), maxlen=0)
    print(f"\nFinished after {len(store['history'])} steps.")


if __name__ == "__main__":
    main()
