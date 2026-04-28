import os
import random
from datetime import datetime
from typing import List, Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def call_llm(prompt: str, model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content


def fake_inbox() -> List[str]:
    """Stand-in mail server. Random 0-2 messages per call."""
    return [
        f"[{datetime.now().strftime('%H:%M:%S')}] mock email #{random.randint(1, 999)}: status check pending"
        for _ in range(random.randint(0, 2))
    ]
