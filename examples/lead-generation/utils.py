import os
from typing import List, Dict, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(model=model, messages=messages).choices[0].message.content


SAMPLE_LEADS = [
    {"name": "Alex Rivera", "title": "VP Engineering", "company": "Stratoscale"},
    {"name": "Priya Menon", "title": "Senior Software Engineer", "company": "Helio Labs"},
    {"name": "Daniel Kim", "title": "Marketing Coordinator", "company": "Brightline"},
    {"name": "Mei Tanaka", "title": "CTO", "company": "QuanthAI"},
    {"name": "Liam O'Connor", "title": "Junior Designer", "company": "PixelCrate"},
]
