"""Thin wrapper around OpenAI embeddings — the tool layer."""

import os
from typing import List, Optional

import numpy as np
from openai import OpenAI


_client: Optional[OpenAI] = None


def embed(texts: List[str], model: str = "text-embedding-3-small") -> np.ndarray:
    global _client
    if _client is None:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = _client.embeddings.create(model=model, input=texts)
    return np.stack([np.array(d.embedding, dtype="float32") for d in resp.data])
