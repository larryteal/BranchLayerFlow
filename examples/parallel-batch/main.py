import asyncio
import time
from pathlib import Path

from flow import build_parallel_translate_flow


async def main() -> None:
    here = Path(__file__).parent
    source = (here / "source.md")
    if not source.exists():
        source.write_text(
            "# Demo\n\nA small markdown doc to demo parallel translation.\n",
            encoding="utf-8",
        )

    out_dir = here / "translations"
    out_dir.mkdir(exist_ok=True)

    store = {
        "source": source.read_text(encoding="utf-8"),
        "out_dir": str(out_dir),
        "written": [],
    }

    flow = build_parallel_translate_flow()
    started = time.time()
    print(f"Translating into {len(flow.branches)} languages in parallel...")
    async for _ in flow(store=store):
        pass
    print(f"\nDone in {time.time() - started:.1f}s — {len(store['written'])} files.")


if __name__ == "__main__":
    asyncio.run(main())
