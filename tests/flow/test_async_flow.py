from typing import Any, Tuple, Optional
from branchlayerflow import BaseMeta, AsyncBaseAgent, AsyncBaseFlow
import pytest

class Meta(BaseMeta):
    pass

class AddAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["x"] += 1
    
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return self.successors["echo_agent"],
    
class EchoAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        print(store)

class MasterFlow(AsyncBaseFlow):
    async def takeover(self, store: Any) -> None:
        print("-------------------start-----------------")
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent]]:
        print("-------------------done-----------------")


@pytest.fixture
def master_flow():
    add_agent = AddAgent(meta=Meta(**{ "name": "add_agent" }))
    echo_agent = EchoAgent(meta=Meta(**{ "name": "echo_agent" }))
    add_agent >> echo_agent # type: ignore
    master_flow = MasterFlow(meta=Meta(**{ "name": "master_flow" }), branches=(add_agent,))
    return master_flow

store = { "x": 0 }

@pytest.mark.asyncio
async def test_iter(master_flow):
    assert master_flow.n_branches == 1
    async for _ in master_flow(store=store):
        pass
    assert master_flow.n_branches == 0

def test_store_result():
    assert store["x"] == 1
