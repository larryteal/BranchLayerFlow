from branchlayerflow import BaseMeta, AsyncBaseAgent
from types import AsyncGeneratorType
import pytest

@pytest.fixture
def agent():
    return AsyncBaseAgent(meta=BaseMeta(**{ "name": "async_base_agent" }))

def test_initial_value():
    agent = AsyncBaseAgent(meta=BaseMeta(**{ "name": "async_base_agent" }))
    assert isinstance(agent.meta, BaseMeta)
    assert agent.meta.name == "async_base_agent"
    assert agent.successors == {}
    assert agent.parent_flow is None

def test_meta_attribute(agent):
    with pytest.raises(AttributeError):
        agent.meta = BaseMeta(**{ "name": "test_async_base_agent" })

@pytest.mark.asyncio
async def test_takeover(agent):
    result = await agent.takeover(store=None)
    assert result == None

@pytest.mark.asyncio
async def test__takeover(agent):
    result = await agent._takeover(store=None)
    assert result == None

@pytest.mark.asyncio
async def test_handoff(agent):
    result = await agent.handoff(store=None)
    assert result == None

@pytest.mark.asyncio
async def test__handoff(agent):
    result = await agent._handoff(store=None)
    assert result == None

@pytest.mark.asyncio
async def test_call(agent):
    agent_iter = agent(store=None)
    assert isinstance(agent_iter, AsyncGeneratorType)

@pytest.mark.asyncio
async def test_iter(agent):
    agent_iter = agent(store=None)
    result = await agent_iter.__anext__()
    assert result == ()
    with pytest.raises(StopAsyncIteration):
        await agent_iter.__anext__()

def test_rshift(agent):
    successor = AsyncBaseAgent(meta=BaseMeta(**{ "name": "successor_agent" }))
    agent >> successor # type: ignore
    assert "successor_agent" in agent.successors
    assert id(agent.successors["successor_agent"]) == id(successor)
