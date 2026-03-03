from typing import Any, Tuple, Optional
from branchlayerflow import BaseMeta, AsyncBaseAgent
from types import AsyncGeneratorType
import pytest


successor_agent = AsyncBaseAgent(meta=BaseMeta(**{ "name": "successor_agent" }))
store = { "x": 1 }

class Agent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["x"] += 1

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        store["x"] += 1
        return successor_agent,

@pytest.fixture
def agent():
    return Agent(meta=BaseMeta(**{ "name": "async_agent" }))

@pytest.mark.asyncio
async def test_iter(agent):
    agent_iter = agent(store=store)
    assert isinstance(agent_iter, AsyncGeneratorType)
    result = await agent_iter.__anext__()
    assert result == (successor_agent,)
    with pytest.raises(StopAsyncIteration):
        await agent_iter.__anext__()

def test_store_result():
    assert store["x"] == 3
