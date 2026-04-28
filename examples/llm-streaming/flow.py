"""Streaming LLM with ENTER-to-interrupt.

A single agent owns the stream. A daemon thread watches stdin; pressing
ENTER sets an Event and the streaming loop bails out. Whatever was
accumulated before interrupt is what gets stored.
"""

import os
import sys
import threading
from typing import Any

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import stream_fake, stream_real


def _start_interrupt_listener() -> threading.Event:
    interrupted = threading.Event()
    if not sys.stdin.isatty():
        return interrupted  # non-interactive: never trip

    def listen():
        try:
            sys.stdin.readline()
        except Exception:
            pass
        interrupted.set()

    threading.Thread(target=listen, daemon=True).start()
    return interrupted


class StreamAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        use_real = bool(os.environ.get("USE_REAL_LLM"))
        producer = stream_real if use_real else stream_fake
        interrupted = _start_interrupt_listener()

        accumulated = []
        for chunk in producer(store["prompt"]):
            if interrupted.is_set():
                print("\n[interrupted]")
                break
            print(chunk, end="", flush=True)
            accumulated.append(chunk)
        else:
            print()
        store["response"] = "".join(accumulated)


def build_stream_flow() -> BaseFlow:
    s = StreamAgent(meta=BaseMeta(name="stream"))
    return BaseFlow(meta=BaseMeta(name="stream_flow"), branches=(s,))
