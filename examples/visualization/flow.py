"""Toy order-processing flow: payment -> inventory -> shipping."""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta


def _make_step(name: str, key: str):
    class _Step(BaseAgent):
        def takeover(self, store: Any) -> None:
            store[key] = "done"
        def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
            return tuple(self.successors.values())[:1]
    _Step.__name__ = name.capitalize() + "Agent"
    return _Step


def build_payment_flow() -> BaseFlow:
    Auth = _make_step("auth", "auth_ok")
    Charge = _make_step("charge", "charged")
    auth = Auth(meta=BaseMeta(name="auth"))
    charge = Charge(meta=BaseMeta(name="charge"))
    auth >> charge
    return BaseFlow(meta=BaseMeta(name="payment_flow"), branches=(auth,))


def build_inventory_flow() -> BaseFlow:
    Reserve = _make_step("reserve", "reserved")
    Pick = _make_step("pick", "picked")
    r = Reserve(meta=BaseMeta(name="reserve"))
    p = Pick(meta=BaseMeta(name="pick"))
    r >> p
    return BaseFlow(meta=BaseMeta(name="inventory_flow"), branches=(r,))


def build_shipping_flow() -> BaseFlow:
    Pack = _make_step("pack", "packed")
    Ship = _make_step("ship", "shipped")
    pa = Pack(meta=BaseMeta(name="pack"))
    sh = Ship(meta=BaseMeta(name="ship"))
    pa >> sh
    return BaseFlow(meta=BaseMeta(name="shipping_flow"), branches=(pa,))


def build_order_flow() -> BaseFlow:
    pay = build_payment_flow()
    inv = build_inventory_flow()
    shi = build_shipping_flow()
    pay >> inv
    inv >> shi
    return BaseFlow(meta=BaseMeta(name="order_flow"), branches=(pay,))
