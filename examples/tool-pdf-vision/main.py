import os
import sys
from collections import deque
from pathlib import Path

from flow import build_pdf_flow


def main() -> None:
    pdf_path = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PDF_PATH", ""))
    if not pdf_path or not pdf_path.exists():
        print("Usage: main.py <pdf-path>  (or set PDF_PATH env var)")
        sys.exit(1)
    store = {"pdf_path": str(pdf_path), "instruction": "Extract all text verbatim, preserving structure."}
    deque(build_pdf_flow()(store=store), maxlen=0)
    print("\n--- Extracted text ---\n")
    print(store["text"])


if __name__ == "__main__":
    main()
