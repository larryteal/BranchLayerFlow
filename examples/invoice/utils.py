import base64
import io
import os
from pathlib import Path
from typing import List, Optional

from openai import OpenAI
from pdf2image import convert_from_path
from PIL import Image


_client: Optional[OpenAI] = None


def render_pdf(path: Path) -> List[Image.Image]:
    return convert_from_path(str(path), dpi=150)


def vision_extract_yaml(image: Image.Image) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    buf = io.BytesIO()
    image.save(buf, "PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "Extract this invoice as YAML with keys: vendor, customer, "
                    "tax_rate (decimal), line_items (list of {description, qty, "
                    "unit_price, amount}), subtotal, tax, total. "
                    "Return ONLY YAML, no fencing."
                )},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
    )
    return resp.choices[0].message.content
