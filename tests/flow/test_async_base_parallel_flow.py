from branchlayerflow import BaseMeta, AsyncParallelBaseFlow
from types import AsyncGeneratorType
import pytest

@pytest.fixture
def flow():
    return AsyncParallelBaseFlow(meta=BaseMeta(**{ "name": "async_base_flow" }), branches=())

def test_initial_value():
    flow = AsyncParallelBaseFlow(meta=BaseMeta(**{ "name": "async_base_flow" }), branches=())
    assert isinstance(flow.meta, BaseMeta)
    assert flow.meta.name == "async_base_flow"
    assert flow.successors == {}
    assert flow.parent_flow is None
    assert flow.branches == ()
    assert flow.n_branches == 0

def test_meta_attribute(flow):
    with pytest.raises(AttributeError):
        flow.meta = BaseMeta(**{ "name": "test_async_base_flow" })

@pytest.mark.asyncio
async def test_takeover(flow):
    result = await flow.takeover(store=None)
    assert result == None

@pytest.mark.asyncio
async def test__takeover(flow):
    result = await flow._takeover(store=None)
    assert result == None

@pytest.mark.asyncio
async def test_handoff(flow):
    result = await flow.handoff(store=None)
    assert result == None

@pytest.mark.asyncio
async def test__handoff(flow):
    result = await flow._handoff(store=None)
    assert result == None

def test_call(flow):
    flow_iter = flow(store=None)
    assert isinstance(flow_iter, AsyncGeneratorType)

@pytest.mark.asyncio
async def test_iter(flow):
    flow_iter = flow(store=None)
    result = await flow_iter.__anext__()
    assert result == ()
    result = await flow_iter.__anext__()
    assert result == ()
    with pytest.raises(StopAsyncIteration):
        await flow_iter.__anext__()

def test_rshift(flow):
    successor = AsyncParallelBaseFlow(meta=BaseMeta(**{ "name": "successor_flow" }), branches=())
    flow >> successor # type: ignore
    assert "successor_flow" in flow.successors
    assert id(flow.successors["successor_flow"]) == id(successor)
