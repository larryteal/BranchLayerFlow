"""Six tools the agent can call."""

import subprocess
from pathlib import Path
from typing import List


def list_files(root: Path) -> List[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())


def grep_search(root: Path, pattern: str) -> List[str]:
    hits = []
    for path in root.rglob("*.py"):
        for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if pattern in line:
                hits.append(f"{path.relative_to(root)}:{i}: {line.strip()}")
    return hits[:50]


def read_file(root: Path, rel_path: str) -> str:
    return (root / rel_path).read_text(errors="replace")


def patch_file(root: Path, rel_path: str, search: str, replace: str) -> str:
    """Read-validate-apply. Validation = `search` must appear exactly once."""
    p = root / rel_path
    text = p.read_text()
    count = text.count(search)
    if count != 1:
        return f"ERROR: search string appears {count} time(s) in {rel_path}"
    p.write_text(text.replace(search, replace, 1))
    return f"OK: patched {rel_path}"


def run_command(root: Path, cmd: str) -> str:
    proc = subprocess.run(
        cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=60
    )
    return f"exit={proc.returncode}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"


def done(message: str) -> str:
    return f"DONE: {message}"
