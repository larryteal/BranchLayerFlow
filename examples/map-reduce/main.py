import asyncio
from pathlib import Path

from flow import build_map_reduce_flow


SAMPLES = {
    "alice.txt": "Alice — 8y Python, distributed systems, Kafka, Postgres. Led platform team.",
    "bob.txt": "Bob — graphic designer, 5y Photoshop & Figma. Some HTML/CSS.",
    "carol.txt": "Carol — 6y Go and Rust, microservices on Kubernetes. Open-source maintainer.",
    "dave.txt": "Dave — recent CS grad, JavaScript hobby projects, eager to learn.",
    "eve.txt": "Eve — 10y backend engineer, Python, AWS, gRPC. Tech lead at scale-up.",
}


def _seed(dir_: Path) -> None:
    dir_.mkdir(exist_ok=True)
    for name, body in SAMPLES.items():
        p = dir_ / name
        if not p.exists():
            p.write_text(body, encoding="utf-8")


async def main() -> None:
    here = Path(__file__).parent
    resume_dir = here / "resumes"
    _seed(resume_dir)

    flow = build_map_reduce_flow(resume_dir)
    print(f"Evaluating {len(flow.branches)} resumes in parallel...")
    async for _ in flow(store={}):
        pass


if __name__ == "__main__":
    asyncio.run(main())
