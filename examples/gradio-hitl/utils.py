import os
from typing import List, Dict, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(model=model, messages=messages).choices[0].message.content


def fake_weather(city: str) -> str:
    return f"Weather in {city}: 22°C, mostly sunny (mock)"


def fake_booking(city: str) -> str:
    return f"Booked a 2-night hotel stay in {city}, $180 total (mock)"
