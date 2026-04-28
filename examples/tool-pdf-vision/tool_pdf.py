"""PDF -> image -> GPT-4o vision tool."""

import base64
import io
import os
from pathlib import Path
from typing import List, Optional

from openai import OpenAI
from pdf2image import convert_from_path
from PIL import Image


_client: Optional[OpenAI] = None


def pdf_to_images(pdf_path: Path, dpi: int = 150) -> List[Image.Image]:
    return convert_from_path(str(pdf_path), dpi=dpi)


def _img_to_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def vision_extract(img: Image.Image, instruction: str = "Extract all text verbatim.") -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                {"type": "image_url", "image_url": {"url": _img_to_data_url(img)}},
            ],
        }],
    )
    return resp.choices[0].message.content
