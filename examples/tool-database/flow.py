"""Three-agent task-manager workflow that exercises the SQLite tool.

  SeedAgent      (insert sample tasks)
       |
       v
  CompleteAgent  (mark a few tasks done)
       |
       v
  ReportAgent    (print the table)
"""

from pathlib import Path
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from tool_db import add_task, list_tasks, mark_done


class SeedAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        db = Path(store["db_path"])
        store["ids"] = [add_task(db, title) for title in store["initial"]]

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["complete"],)


class CompleteAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        db = Path(store["db_path"])
        for tid in store["ids"][:2]:
            mark_done(db, tid)

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["report"],)


class ReportAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        rows = list_tasks(Path(store["db_path"]))
        print("id  done  title")
        print("--  ----  -----")
        for tid, title, done in rows:
            print(f"{tid:>2}   {'x' if done else ' '}    {title}")


def build_db_flow() -> BaseFlow:
    seed = SeedAgent(meta=BaseMeta(name="seed"))
    cmp_ = CompleteAgent(meta=BaseMeta(name="complete"))
    rep = ReportAgent(meta=BaseMeta(name="report"))
    seed >> cmp_
    cmp_ >> rep
    return BaseFlow(meta=BaseMeta(name="db_flow"), branches=(seed,))
