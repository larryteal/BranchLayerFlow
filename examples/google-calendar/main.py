from collections import deque
from datetime import datetime, timedelta, timezone

from flow import build_calendar_flow


def main() -> None:
    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(hours=1)
    store = {
        "summary": "BLF demo: take a walk",
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
    deque(build_calendar_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
