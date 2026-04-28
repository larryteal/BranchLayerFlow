import os
from pathlib import Path
from typing import List, Dict, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def _c() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    return _c().chat.completions.create(model=model, messages=messages).choices[0].message.content


def tts_to_file(text: str, voice: str, out_path: Path) -> None:
    resp = _c().audio.speech.create(model="tts-1", voice=voice, input=text)
    resp.stream_to_file(str(out_path))
