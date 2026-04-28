from collections import deque
from pathlib import Path

from flow import build_translate_flow


def main() -> None:
    here = Path(__file__).parent
    source_path = here / "source.md"
    if not source_path.exists():
        source_path.write_text(
            "# Demo\n\nThis is a small markdown document used to "
            "showcase batch translation across 8 languages.\n",
            encoding="utf-8",
        )

    out_dir = here / "translations"
    out_dir.mkdir(exist_ok=True)

    store = {
        "source": source_path.read_text(encoding="utf-8"),
        "out_dir": str(out_dir),
        "written": [],
    }

    print("Translating 8 languages sequentially (one at a time)...")
    deque(build_translate_flow()(store=store), maxlen=0)
    print(f"\nWrote {len(store['written'])} files to {out_dir}")


if __name__ == "__main__":
    main()
