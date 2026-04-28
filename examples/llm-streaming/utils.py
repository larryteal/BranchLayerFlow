import os
import time
from typing import Iterable, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def stream_real(prompt: str, model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> Iterable[str]:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    stream = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def stream_fake(prompt: str) -> Iterable[str]:
    text = (
        f"Here is a slow simulated answer to: {prompt!r}. "
        "Press ENTER any time to interrupt this stream and the next "
        "agent will get whatever has accumulated so far."
    )
    for word in text.split():
        time.sleep(0.15)
        yield word + " "
