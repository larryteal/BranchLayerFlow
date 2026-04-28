import base64
import os
from typing import Optional

from openai import OpenAI


_client: Optional[OpenAI] = None


def generate_image_b64(prompt: str, size: str = "1024x1024") -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    img = _client.images.generate(
        model="gpt-image-1", prompt=prompt, size=size, n=1
    ).data[0]
    if getattr(img, "b64_json", None):
        return img.b64_json
    # url fallback
    import requests
    return base64.b64encode(requests.get(img.url, timeout=60).content).decode()
