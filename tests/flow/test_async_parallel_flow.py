from typing import Any, Tuple, Optional
from branchlayerflow import BaseMeta, AsyncBaseAgent, AsyncParallelBaseFlow
import asyncio
import pytest

class Meta(BaseMeta):
    pass

class AddAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        await asyncio.sleep(1)
        store["x"] += 1

class MasterFlow(AsyncParallelBaseFlow):
    async def takeover(self, store: Any) -> None:
        print("-------------------start-----------------")
    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent]]:
        print("-------------------done-----------------")

@pytest.fixture
def master_flow():
    add_agent_1 = AddAgent(meta=Meta(**{ "name": "add_agent_1" }))
    add_agent_2 = AddAgent(meta=Meta(**{ "name": "add_agent_2" }))
    add_agent_3 = AddAgent(meta=Meta(**{ "name": "add_agent_3" }))
    master_flow = MasterFlow(meta=Meta(**{ "name": "master_flow" }), branches=(add_agent_1, add_agent_2, add_agent_3))
    return master_flow

store = { "x": 0 }

@pytest.mark.asyncio
async def test_iter(master_flow):
    assert master_flow.n_branches == 3
    start = asyncio.get_running_loop().time()
    async for _ in master_flow(store=store):
        pass
    end = asyncio.get_running_loop().time()
    assert end - start < 2
    assert master_flow.n_branches == 0

def test_store_result():
    assert store["x"] == 3
