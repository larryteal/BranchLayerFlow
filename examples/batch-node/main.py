import csv
import random
from collections import deque
from pathlib import Path

from flow import build_aggregate_flow


def _make_sample_csv(path: Path, rows: int = 10000) -> None:
    random.seed(0)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "amount"])
        writer.writeheader()
        for i in range(rows):
            writer.writerow({"id": i, "amount": round(random.uniform(1.0, 500.0), 2)})


def main() -> None:
    here = Path(__file__).parent
    csv_path = here / "sales.csv"
    if not csv_path.exists():
        print(f"Generating sample CSV at {csv_path}...")
        _make_sample_csv(csv_path)

    store = {"csv_path": str(csv_path), "chunk_size": 1000, "stats": None}
    deque(build_aggregate_flow()(store=store), maxlen=0)
    s = store["stats"]
    print(
        f"transactions={s['transaction_count']}  "
        f"total=${s['total_sales']:.2f}  "
        f"avg=${s['average_transaction']:.2f}"
    )


if __name__ == "__main__":
    main()
