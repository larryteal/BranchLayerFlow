from typing import Any, Tuple, Optional
from branchlayerflow import BaseMeta, AsyncBaseAgent, AsyncBaseFlow
import pytest

class Meta(BaseMeta):
    pass

class AddAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["x"] += 3

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return self.successors["sub_agent"],

class SubAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["x"] -= 1

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return self.successors["mul_agent"],

class MulAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["x"] *= 3

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return self.successors["div_agent"],

class DivAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["x"] /= 2
    
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return self.successors["echo_agent"],

class EchoAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        print(store)

class FirstNameAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["full_name"] += "Foo"

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return self.successors["lastname_agent"],

class LastNameAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["full_name"] += "Bar"

class FullNameFlow(AsyncBaseFlow):
    async def takeover(self, store: Any) -> None:
        store["full_name"] = ""
        print("-------------------sub flow start-----------------")
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent]]:
        print("-------------------sub flow done-----------------")

class MasterFlow(AsyncBaseFlow):
    async def takeover(self, store: Any) -> None:
        print("-------------------start-----------------")
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent]]:
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

@pytest.mark.asyncio
async def test_iter(master_flow):
    assert master_flow.n_branches == 2
    async for _ in master_flow(store=store):
        pass
    assert master_flow.n_branches == 0

def test_store_result():
    assert store["x"] == 3
    assert store["full_name"] == "FooBar"
