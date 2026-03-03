from typing import Any, Tuple, Optional
from branchlayerflow import BaseMeta, BaseAgent, BaseFlow
from collections import deque
import pytest

class Meta(BaseMeta):
    pass

class AddAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] += 3

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["sub_agent"],

class SubAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] -= 1

class MulAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] *= 3

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["div_agent"],

class DivAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] /= 2

class EchoAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        print(store)

class AddSubFlow(BaseFlow):
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["muldiv_flow"],

class MulDivFlow(BaseFlow):
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["echo_agent"],

class MasterFlow(BaseFlow):
    def takeover(self, store: Any) -> None:
        print("-------------------start-----------------")
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent]]:
        print("-------------------done-----------------")


@pytest.fixture
def master_flow():
    add_agent = AddAgent(meta=Meta(**{ "name": "add_agent" }))
    sub_agent = SubAgent(meta=Meta(**{ "name": "sub_agent" }))
    mul_agent = MulAgent(meta=Meta(**{ "name": "mul_agent" }))
    div_agent = DivAgent(meta=Meta(**{ "name": "div_agent" }))
    echo_agent = EchoAgent(meta=Meta(**{ "name": "echo_agent" }))
    add_agent >> sub_agent # type: ignore
    mul_agent >> div_agent # type: ignore
    addsub_flow = AddSubFlow(meta=Meta(**{ "name": "addsub_flow" }), branches=(add_agent,))
    muldiv_flow = MulDivFlow(meta=Meta(**{ "name": "muldiv_flow" }), branches=(mul_agent,))
    addsub_flow >> muldiv_flow # type: ignore
    muldiv_flow >> echo_agent # type: ignore
    master_flow = MasterFlow(meta=Meta(**{ "name": "master_flow" }), branches=(addsub_flow,))
    return master_flow

def test_flow_attrs(master_flow):
    assert master_flow.n_branches == 1
    assert len(master_flow.branches) == 1
    assert master_flow.branches[0].parent_flow == master_flow

store = { "x": 0 }

def test_iter(master_flow):
    assert master_flow.n_branches == 1
    deque(master_flow(store=store), maxlen=0)
    assert master_flow.n_branches == 0
    assert master_flow.branches[0].n_branches == 0

def test_store_result():
    assert store["x"] == 3
