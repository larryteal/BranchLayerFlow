from typing import Any, Tuple, Optional
from branchlayerflow import BaseMeta, BaseAgent, BaseFlow
from collections import deque
import pytest

class Meta(BaseMeta):
    pass

class AddAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] += 1
    
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["echo_agent"],

class MulAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] *= 2

class EchoAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        print(store)

class MasterFlow(BaseFlow):
    def takeover(self, store: Any) -> None:
        print("-------------------start-----------------")
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent]]:
        print("-------------------done-----------------")


@pytest.fixture
def master_flow():
    add_agent = AddAgent(meta=Meta(**{ "name": "add_agent" }))
    mul_agent = MulAgent(meta=Meta(**{ "name": "mul_agent" }))
    echo_agent = EchoAgent(meta=Meta(**{ "name": "echo_agent" }))
    add_agent >> echo_agent # type: ignore
    master_flow = MasterFlow(meta=Meta(**{ "name": "master_flow" }), branches=(add_agent, mul_agent))
    return master_flow

store = { "x": 0 }

def test_iter(master_flow):
    assert master_flow.n_branches == 2
    deque(master_flow(store=store), maxlen=0)
    assert master_flow.n_branches == 0

def test_store_result():
    assert store["x"] == 2
