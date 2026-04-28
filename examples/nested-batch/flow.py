"""Hierarchical aggregation via nested Flows.

  SchoolFlow                  <-- handoff aggregates class averages
    +-- ClassFlow_a           <-- handoff aggregates student averages
    |     +-- StudentAgent_1  <-- takeover computes per-student average
    |     +-- StudentAgent_2
    |     ...
    +-- ClassFlow_b
          +-- ...

The pattern relies on two BLF facts:
  1. Flow IS Agent, so a Flow can be a branch of another Flow.
  2. A Flow's `handoff` is its closing rite — the natural place to
     aggregate the work its branches just did.
"""

from pathlib import Path
from statistics import mean
from typing import Any

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta


class StudentAgent(BaseAgent):
    """Reads one student file and writes that student's average into the store."""

    def takeover(self, store: Any) -> None:
        path = Path(self.meta.path)
        grades = [float(line) for line in path.read_text().splitlines() if line.strip()]
        avg = mean(grades) if grades else 0.0
        store.setdefault("students", {})[self.meta.student_id] = avg


class ClassFlow(BaseFlow):
    """Aggregates its student branches into a single class average."""

    def handoff(self, store: Any):
        students = store.get("students", {})
        class_id = self.meta.class_id
        class_students = {sid: avg for sid, avg in students.items() if sid.startswith(class_id + "_")}
        class_avg = mean(class_students.values()) if class_students else 0.0
        store.setdefault("class_avgs", {})[class_id] = class_avg
        return None


class SchoolFlow(BaseFlow):
    """Aggregates all class averages into a single school-wide average."""

    def handoff(self, store: Any):
        avgs = store.get("class_avgs", {})
        store["school_avg"] = mean(avgs.values()) if avgs else 0.0
        return None


def build_school_flow(root: Path) -> SchoolFlow:
    class_flows = []
    for class_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        class_id = class_dir.name
        student_agents = tuple(
            StudentAgent(meta=BaseMeta(
                name=f"student_{class_id}_{p.stem}",
                student_id=f"{class_id}_{p.stem}",
                path=str(p),
            ))
            for p in sorted(class_dir.glob("*.txt"))
        )
        class_flows.append(ClassFlow(
            meta=BaseMeta(name=f"class_{class_id}", class_id=class_id),
            branches=student_agents,
        ))
    return SchoolFlow(meta=BaseMeta(name="school"), branches=tuple(class_flows))
