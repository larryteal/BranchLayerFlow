"""Document -> nuggets -> dialogue script -> per-line TTS -> merged mp3."""

import re
from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat, tts_to_file


HOST_VOICES = {"Alex": "alloy", "Jamie": "echo"}
LINE_RE = re.compile(r"^(Alex|Jamie):\s*(.+)$", re.IGNORECASE)


class NuggetsAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["nuggets"] = chat([
            {"role": "system", "content": "Pull 2-3 interesting nuggets from each document section, as a markdown list."},
            {"role": "user", "content": store["document"]},
        ])

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["script"],)


class ScriptAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        raw = chat([
            {"role": "system", "content": (
                "Write a ~12-line conversational podcast script between two hosts named "
                "Alex and Jamie. Each line MUST start with `Alex:` or `Jamie:` only."
            )},
            {"role": "user", "content": store["nuggets"]},
        ])
        store["script"] = [
            (m.group(1).capitalize(), m.group(2).strip())
            for line in raw.splitlines()
            if (m := LINE_RE.match(line.strip()))
        ]

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["synth"],)


class SynthAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        out_dir = Path(store["out_dir"])
        clips_dir = out_dir / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)
        store["clips"] = []
        for i, (host, line) in enumerate(store["script"]):
            voice = HOST_VOICES[host]
            clip = clips_dir / f"{i:03d}_{host}.mp3"
            tts_to_file(line, voice, clip)
            store["clips"].append(str(clip))
            print(f"  [{host}] {line[:80]}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["merge"],)


class MergeAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        from pydub import AudioSegment  # type: ignore
        merged = AudioSegment.silent(duration=400)
        for clip in store["clips"]:
            merged += AudioSegment.from_file(clip) + AudioSegment.silent(duration=300)
        out = Path(store["out_dir"]) / "podcast.mp3"
        merged.export(out, format="mp3")
        store["mp3"] = str(out)
        print(f"\nWrote {out}")


def build_podcast_flow() -> BaseFlow:
    n = NuggetsAgent(meta=BaseMeta(name="nuggets"))
    s = ScriptAgent(meta=BaseMeta(name="script"))
    sy = SynthAgent(meta=BaseMeta(name="synth"))
    m = MergeAgent(meta=BaseMeta(name="merge"))
    n >> s
    s >> sy
    sy >> m
    return BaseFlow(meta=BaseMeta(name="podcast_flow"), branches=(n,))
