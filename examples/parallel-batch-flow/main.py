import asyncio
import random
import time
from pathlib import Path

from PIL import Image

from flow import FILTERS, build_parallel_batch_flow


def _make_sample_images(out_dir: Path, count: int = 3) -> list[str]:
    random.seed(0)
    paths = []
    for i in range(count):
        path = out_dir / f"sample_{i}.png"
        if not path.exists():
            img = Image.new("RGB", (256, 256))
            img.putdata([
                (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                for _ in range(256 * 256)
            ])
            img.save(path)
        paths.append(str(path))
    return paths


async def main() -> None:
    here = Path(__file__).parent
    src_dir = here / "samples"
    src_dir.mkdir(exist_ok=True)
    image_paths = _make_sample_images(src_dir)

    out_dir = here / "out"
    out_dir.mkdir(exist_ok=True)

    flow = build_parallel_batch_flow(image_paths, list(FILTERS.keys()), out_dir)
    started = time.time()
    print(f"Processing {len(flow.branches)} pairs in parallel...")
    async for _ in flow(store={}):
        pass
    print(f"\nDone in {time.time() - started:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
