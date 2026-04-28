import os
import random
from typing import Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def call_llm(prompt: str, model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content


def fake_search(query: str) -> str:
    """Stand-in web search — returns canned snippets so the demo runs offline."""
    return (
        f"Wikipedia: {query} — A concise overview describing relevant context "
        f"and basic facts about {query}. (placeholder snippet)"
    )


def maybe_garble(text: str, p: float = 0.5) -> str:
    """Inner agent's unreliability: 50% chance of producing nonsense."""
    if random.random() < p:
        return "asdfgh qwerty zxcvbn — gibberish answer (intentionally bad for demo)"
    return text
