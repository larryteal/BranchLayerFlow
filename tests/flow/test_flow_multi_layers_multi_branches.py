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

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["mul_agent"],

class MulAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] *= 3

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["div_agent"],

class DivAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] /= 2
    
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["echo_agent"],

class EchoAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        print(store)

class FirstNameAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["full_name"] += "Foo"

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.successors["lastname_agent"],

class LastNameAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["full_name"] += "Bar"

class FullNameFlow(BaseFlow):
    def takeover(self, store: Any) -> None:
        store["full_name"] = ""
        print("-------------------sub flow start-----------------")
    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent]]:
        print("-------------------sub flow done-----------------")

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
    firstname_agent = FirstNameAgent(meta=Meta(**{ "name": "firstname_agent" }))
    lastname_agent = LastNameAgent(meta=Meta(**{ "name": "lastname_agent" }))
    echo_agent = EchoAgent(meta=Meta(**{ "name": "echo_agent" }))
    add_agent >> sub_agent # type: ignore
    sub_agent >> mul_agent # type: ignore
    mul_agent >> div_agent # type: ignore
    div_agent >> echo_agent # type: ignore
    firstname_agent >> lastname_agent # type: ignore
    lastname_agent >> echo_agent # type: ignore
    fullname_flow = FullNameFlow(meta=Meta(**{ "name": "fullname_flow" }), branches=(firstname_agent,))
    master_flow = MasterFlow(meta=Meta(**{ "name": "master_flow" }), branches=(add_agent, fullname_flow))
    return master_flow

store = { "x": 0 }

def test_iter(master_flow):
    assert master_flow.n_branches == 2
    deque(master_flow(store=store), maxlen=0)
    assert master_flow.n_branches == 0

def test_store_result():
    assert store["x"] == 3
    assert store["full_name"] == "FooBar"
