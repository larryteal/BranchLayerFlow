import os
from typing import List, Dict, Optional

import numpy as np
from openai import OpenAI


_client: Optional[OpenAI] = None


def _c() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def chat(messages: List[Dict[str, str]], model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    return _c().chat.completions.create(model=model, messages=messages).choices[0].message.content


def embed(text: str, model: str = "text-embedding-3-small") -> np.ndarray:
    return np.array(_c().embeddings.create(model=model, input=text).data[0].embedding, dtype="float32")
