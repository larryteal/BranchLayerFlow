"""NL -> SQL with self-debug loop.

  SchemaAgent     (introspect SQLite schema)
       |
       v
  GenerateAgent   (NL -> SQL using schema)
       |
       v
  ExecuteAgent    (run; on error -> DebugAgent)
       |
       +--[ok]---> ()
       +--[err]--> DebugAgent --> GenerateAgent (loop)
"""

import sqlite3
from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat, strip_sql_fence


class SchemaAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        with sqlite3.connect(store["db_path"]) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            schema_lines = []
            for (t,) in tables:
                cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
                col_str = ", ".join(f"{c[1]} {c[2]}" for c in cols)
                schema_lines.append(f"{t}({col_str})")
        store["schema"] = "\n".join(schema_lines)
        print(f"schema:\n{store['schema']}\n")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["generate"],)


class GenerateAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        prompt = (
            f"Database schema:\n{store['schema']}\n\n"
            f"Question: {store['question']}\n\n"
        )
        if store.get("last_error"):
            prompt += f"Previous SQL failed:\n{store['last_sql']}\nError: {store['last_error']}\nFix it.\n\n"
        prompt += "Reply with SQLite SQL only."
        store["sql"] = strip_sql_fence(chat([
            {"role": "system", "content": "You write correct SQLite queries."},
            {"role": "user", "content": prompt},
        ]))
        print(f"SQL: {store['sql']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["execute"],)


class ExecuteAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["attempts"] = store.get("attempts", 0) + 1
        try:
            with sqlite3.connect(store["db_path"]) as conn:
                rows = conn.execute(store["sql"]).fetchall()
            store["rows"] = rows
            store["last_error"] = None
            print(f"rows: {rows}")
        except sqlite3.Error as exc:
            store["last_sql"] = store["sql"]
            store["last_error"] = str(exc)
            print(f"ERROR: {exc}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["last_error"] is None or store["attempts"] >= self.meta.max_attempts:
            return ()
        return (self.successors["generate"],)


def build_text2sql_flow(max_attempts: int = 3) -> BaseFlow:
    schema = SchemaAgent(meta=BaseMeta(name="schema"))
    gen = GenerateAgent(meta=BaseMeta(name="generate"))
    exe = ExecuteAgent(meta=BaseMeta(name="execute", max_attempts=max_attempts))
    schema >> gen
    gen >> exe
    exe >> gen
    return BaseFlow(meta=BaseMeta(name="text2sql_flow"), branches=(schema,))
