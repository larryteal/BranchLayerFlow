"""Vision OCR -> arithmetic validation.

  RasterAgent   (PDF -> images)
       |
       v
  ExtractAgent  (per-page YAML extraction; merge into one record)
       |
       v
  ValidateAgent (recompute line totals / subtotal / tax / grand total)
"""

from pathlib import Path
from typing import Any, Optional, Tuple

import yaml
from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import render_pdf, vision_extract_yaml


def _strip_fence(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            body = parts[1]
            if body.startswith("yaml"):
                body = body[4:]
            return body
    return text


class RasterAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["pages"] = render_pdf(Path(store["pdf_path"]))
        print(f"rendered {len(store['pages'])} pages")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["extract"],)


class ExtractAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        merged: dict = {"line_items": []}
        for img in store["pages"]:
            data = yaml.safe_load(_strip_fence(vision_extract_yaml(img))) or {}
            merged.setdefault("vendor", data.get("vendor"))
            merged.setdefault("customer", data.get("customer"))
            merged["tax_rate"] = data.get("tax_rate", merged.get("tax_rate", 0.0))
            merged["line_items"].extend(data.get("line_items") or [])
            for k in ("subtotal", "tax", "total"):
                merged[k] = data.get(k, merged.get(k))
        store["invoice"] = merged

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["validate"],)


class ValidateAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        inv = store["invoice"]
        errors = []
        for li in inv.get("line_items", []):
            try:
                expected = float(li["qty"]) * float(li["unit_price"])
                if abs(expected - float(li["amount"])) > 0.01:
                    errors.append(f"line {li!r}: qty*price={expected:.2f} != amount={li['amount']}")
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"line {li!r}: malformed ({exc})")
        try:
            subtotal_calc = sum(float(li["amount"]) for li in inv["line_items"])
            if abs(subtotal_calc - float(inv["subtotal"])) > 0.01:
                errors.append(f"subtotal: sum={subtotal_calc:.2f} != stated={inv['subtotal']}")
            tax_calc = subtotal_calc * float(inv.get("tax_rate", 0.0))
            if abs(tax_calc - float(inv["tax"])) > 0.05:
                errors.append(f"tax: {tax_calc:.2f} != stated={inv['tax']}")
            total_calc = subtotal_calc + tax_calc
            if abs(total_calc - float(inv["total"])) > 0.05:
                errors.append(f"total: {total_calc:.2f} != stated={inv['total']}")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"totals: malformed ({exc})")
        store["validation_errors"] = errors
        print(f"\nValidation errors: {len(errors)}")
        for e in errors:
            print(f"  - {e}")


def build_invoice_flow() -> BaseFlow:
    raster = RasterAgent(meta=BaseMeta(name="raster"))
    extract = ExtractAgent(meta=BaseMeta(name="extract"))
    validate = ValidateAgent(meta=BaseMeta(name="validate"))
    raster >> extract
    extract >> validate
    return BaseFlow(meta=BaseMeta(name="invoice_flow"), branches=(raster,))
