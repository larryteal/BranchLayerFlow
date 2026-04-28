# Tool — PDF Vision OCR

Renders a PDF to images via `pdf2image` (which depends on `poppler-utils`), then sends each page to GPT-4o vision for verbatim extraction.

## Demonstrates

- Multi-stage tool pipeline: rasterisation → vision extraction
- Per-page work serialised inside one agent; trivial to swap to `AsyncParallelBaseFlow` if you want parallel calls

## Run

```bash
brew install poppler              # or apt-get install poppler-utils
export OPENAI_API_KEY=sk-...
uv run --project examples/tool-pdf-vision python examples/tool-pdf-vision/main.py path/to/file.pdf
```
