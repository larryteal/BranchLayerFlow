"""ListCalendarsAgent -> CreateEventAgent."""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from calendar_tool import create_event, list_calendars


class ListAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["calendars"] = list_calendars()
        for c in store["calendars"]:
            print(f"  {c['summary']}  ({c['id']})")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["create"],)


class CreateAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        cal_id = store.get("target_calendar") or store["calendars"][0]["id"]
        eid = create_event(cal_id, store["summary"], store["start"], store["end"])
        store["event_id"] = eid
        print(f"created event {eid} in {cal_id}")


def build_calendar_flow() -> BaseFlow:
    l = ListAgent(meta=BaseMeta(name="list"))
    c = CreateAgent(meta=BaseMeta(name="create"))
    l >> c
    return BaseFlow(meta=BaseMeta(name="calendar_flow"), branches=(l,))
