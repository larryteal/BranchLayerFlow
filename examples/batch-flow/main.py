import random
from collections import deque
from pathlib import Path

from PIL import Image

from flow import FILTERS, build_batch_flow


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


def main() -> None:
    here = Path(__file__).parent
    src_dir = here / "samples"
    src_dir.mkdir(exist_ok=True)
    image_paths = _make_sample_images(src_dir)

    out_dir = here / "out"
    out_dir.mkdir(exist_ok=True)

    store = {
        "image_paths": image_paths,
        "filters": list(FILTERS.keys()),
        "out_dir": str(out_dir),
        "sub_stores": [],
    }
    print(f"Processing {len(image_paths)} images x {len(store['filters'])} filters...")
    deque(build_batch_flow()(store=store), maxlen=0)
    print(f"\nDone. {len(store['sub_stores'])} outputs in {out_dir}/")


if __name__ == "__main__":
    main()
