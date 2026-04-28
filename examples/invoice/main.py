import os
import sys
from collections import deque
from pathlib import Path
from pprint import pprint

from flow import build_invoice_flow


def main() -> None:
    pdf = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("INVOICE_PDF", ""))
    if not pdf or not pdf.exists():
        print("Usage: main.py <invoice.pdf>  (or set INVOICE_PDF env var)")
        sys.exit(1)
    store = {"pdf_path": str(pdf)}
    deque(build_invoice_flow()(store=store), maxlen=0)
    print("\n--- Invoice ---")
    pprint(store["invoice"])


if __name__ == "__main__":
    main()
