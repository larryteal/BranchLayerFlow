"""Routing flow: classify user message -> dispatch to the right handler."""

import re
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat, fake_booking, fake_weather


CITY_RE = re.compile(r"\bin\s+([A-Z][a-zA-Z\- ]+?)(?:\W|$)")


class RouteAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        decision = chat([
            {"role": "system", "content": (
                "Classify the user message. Reply with EXACTLY one word: "
                "WEATHER, BOOKING, or FOLLOWUP."
            )},
            {"role": "user", "content": store["user_text"]},
        ]).strip().upper()
        store["route"] = decision

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        route = store["route"]
        if "WEATHER" in route:
            return (self.successors["weather"],)
        if "BOOKING" in route:
            return (self.successors["booking"],)
        return (self.successors["followup"],)


def _city(text: str) -> str:
    m = CITY_RE.search(text)
    return m.group(1).strip() if m else "Tokyo"


class WeatherAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["reply"] = fake_weather(_city(store["user_text"]))


class BookingAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["reply"] = fake_booking(_city(store["user_text"]))


class FollowupAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["reply"] = chat([
            {"role": "system", "content": "You are a helpful travel assistant. Reply concisely."},
            {"role": "user", "content": store["user_text"]},
        ])


def build_router_flow() -> BaseFlow:
    r = RouteAgent(meta=BaseMeta(name="route"))
    w = WeatherAgent(meta=BaseMeta(name="weather"))
    b = BookingAgent(meta=BaseMeta(name="booking"))
    f = FollowupAgent(meta=BaseMeta(name="followup"))
    r >> w
    r >> b
    r >> f
    return BaseFlow(meta=BaseMeta(name="router_flow"), branches=(r,))
