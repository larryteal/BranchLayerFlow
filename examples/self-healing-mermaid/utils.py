import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from openai import OpenAI


_client: Optional[OpenAI] = None


def call_llm(prompt: str, model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content


def strip_fence(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            body = parts[i]
            if body.startswith("mermaid"):
                body = body[7:]
            return body.strip()
    return text.strip()


def compile_mermaid(diagram: str) -> Tuple[bool, str]:
    """Compile via `mmdc`. Returns (ok, message). Falls back to a heuristic check
    if mmdc is not on PATH so the demo still works."""
    if shutil.which("mmdc") is None:
        # Heuristic: must start with a known directive.
        if not diagram.strip().splitlines():
            return False, "empty diagram"
        first = diagram.strip().splitlines()[0].strip().lower()
        ok = any(first.startswith(p) for p in (
            "graph", "flowchart", "sequencediagram", "classdiagram",
            "statediagram", "journey", "gantt", "erdiagram", "pie",
            "mindmap", "timeline",
        ))
        return ok, "ok (mmdc missing; heuristic check)" if ok else "diagram missing valid directive header"
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.mmd"
        out = Path(td) / "out.svg"
        src.write_text(diagram, encoding="utf-8")
        proc = subprocess.run(["mmdc", "-i", str(src), "-o", str(out)], capture_output=True, text=True)
        return proc.returncode == 0, (proc.stderr or proc.stdout).strip()
