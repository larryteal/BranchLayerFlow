"""Tiny SQLite tool with parameterised queries and a context-managed connection."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Tuple


SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT NOT NULL,
    done    INTEGER NOT NULL DEFAULT 0
);
"""


@contextmanager
def open_db(path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(path)
    try:
        conn.execute(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_task(db: Path, title: str) -> int:
    with open_db(db) as conn:
        cur = conn.execute("INSERT INTO tasks(title) VALUES (?)", (title,))
        return cur.lastrowid


def mark_done(db: Path, task_id: int) -> None:
    with open_db(db) as conn:
        conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))


def list_tasks(db: Path) -> List[Tuple[int, str, bool]]:
    with open_db(db) as conn:
        return [(row[0], row[1], bool(row[2])) for row in conn.execute("SELECT id, title, done FROM tasks ORDER BY id")]
