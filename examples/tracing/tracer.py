"""Tracing as a BLF subclass.

`@traced` returns a subclass whose `_takeover` and `_handoff` wrap the
inner methods with timing + sink emission. The tracer is the canonical
example of "cross-cutting concerns are subclasses, not plugins."
"""

import time
import uuid
from typing import Any, Callable, Optional, Tuple


class Sink:
    def __init__(self) -> None:
        self.events: list = []

    def emit(self, event: dict) -> None:
        self.events.append(event)
        when = event["t"].strftime("%H:%M:%S.%f")[:-3]
        if event["kind"] == "takeover":
            print(f"  [{when}] takeover  {event['agent']:<14}  {event['dt_ms']:.1f}ms")
        else:
            n = len(event.get("next", ()))
            print(f"  [{when}] handoff   {event['agent']:<14}  {event['dt_ms']:.1f}ms  -> {n} next")


def traced(cls, sink: Sink):
    """Return a subclass of `cls` whose lifecycle is sent to `sink`."""
    from datetime import datetime

    class Traced(cls):  # type: ignore[misc, valid-type]
        def _takeover(self, store: Any) -> None:
            t0 = time.perf_counter()
            super()._takeover(store)
            sink.emit({
                "t": datetime.now(),
                "kind": "takeover",
                "agent": self.meta.name,
                "dt_ms": (time.perf_counter() - t0) * 1000,
            })

        def _handoff(self, store: Any) -> Optional[Tuple[Any, ...]]:
            t0 = time.perf_counter()
            result = super()._handoff(store)
            sink.emit({
                "t": datetime.now(),
                "kind": "handoff",
                "agent": self.meta.name,
                "dt_ms": (time.perf_counter() - t0) * 1000,
                "next": result or (),
            })
            return result

    Traced.__name__ = f"Traced{cls.__name__}"
    return Traced
