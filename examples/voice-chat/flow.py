"""Voice chat: listen -> transcribe -> chat -> speak, looping.

  ListenAgent     (mic -> wav with VAD)
       |
       v
  TranscribeAgent (whisper)
       |
       v
  ReplyAgent      (gpt -> reply text)
       |
       v
  SpeakAgent      (tts -> audio out; loop back unless user said 'exit')
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from audio import record_until_silent, speak, transcribe
from utils import chat


class ListenAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["audio"] = record_until_silent()

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["transcribe"],)


class TranscribeAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["user_text"] = transcribe(store["audio"]).strip()
        print(f"You: {store['user_text']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["reply"],)


class ReplyAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store.setdefault("messages", [])
        store["messages"].append({"role": "user", "content": store["user_text"]})
        text = chat(store["messages"])
        store["messages"].append({"role": "assistant", "content": text})
        store["assistant_text"] = text
        print(f"Assistant: {text}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["speak"],)


class SpeakAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        speak(store["assistant_text"])

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if "exit" in store["user_text"].lower():
            return ()
        return (self.successors["listen"],)


def build_voice_flow() -> BaseFlow:
    L, T, R, S = ListenAgent, TranscribeAgent, ReplyAgent, SpeakAgent
    listen = L(meta=BaseMeta(name="listen"))
    trans = T(meta=BaseMeta(name="transcribe"))
    reply = R(meta=BaseMeta(name="reply"))
    spk = S(meta=BaseMeta(name="speak"))
    listen >> trans
    trans >> reply
    reply >> spk
    spk >> listen
    return BaseFlow(meta=BaseMeta(name="voice_flow"), branches=(listen,))
