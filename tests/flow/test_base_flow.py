from branchlayerflow import BaseMeta, BaseFlow
from types import GeneratorType
import pytest

@pytest.fixture
def flow():
    return BaseFlow(meta=BaseMeta(**{ "name": "base_flow" }), branches=())

def test_initial_value():
    flow = BaseFlow(meta=BaseMeta(**{ "name": "base_flow" }), branches=())
    assert isinstance(flow.meta, BaseMeta)
    assert flow.meta.name == "base_flow"
    assert flow.successors == {}
    assert flow.parent_flow is None
    assert flow.branches == ()
    assert flow.n_branches == 0

def test_meta_attribute(flow):
    with pytest.raises(AttributeError):
        flow.meta = BaseMeta(**{ "name": "test_base_flow" })

def test_takeover(flow):
    result = flow.takeover(store=None)
    assert result == None

def test__takeover(flow):
    result = flow._takeover(store=None)
    assert result == None

def test_handoff(flow):
    result = flow.handoff(store=None)
    assert result == None

def test__handoff(flow):
    result = flow._handoff(store=None)
    assert result == None

def test_call(flow):
    flow_iter = flow(store=None)
    assert isinstance(flow_iter, GeneratorType)

def test_iter(flow):
    flow_iter = flow(store=None)
    result = flow_iter.__next__()
    assert result == ()
    result = flow_iter.__next__()
    assert result == ()
    with pytest.raises(StopIteration):
        flow_iter.__next__()

def test_rshift(flow):
    successor = BaseFlow(meta=BaseMeta(**{ "name": "successor_flow" }), branches=())
    flow >> successor # type: ignore
    assert "successor_flow" in flow.successors
    assert id(flow.successors["successor_flow"]) == id(successor)
