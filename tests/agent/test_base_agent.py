from branchlayerflow import BaseMeta, BaseAgent
from types import GeneratorType
import pytest

@pytest.fixture
def agent():
    return BaseAgent(meta=BaseMeta(**{ "name": "base_agent" }))

def test_initial_value():
    agent = BaseAgent(meta=BaseMeta(**{ "name": "base_agent" }))
    assert isinstance(agent.meta, BaseMeta)
    assert agent.meta.name == "base_agent"
    assert agent.successors == {}
    assert agent.parent_flow is None

def test_meta_attribute(agent):
    with pytest.raises(AttributeError):
        agent.meta = BaseMeta(**{ "name": "test_base_agent" })

def test_takeover(agent):
    result = agent.takeover(store=None)
    assert result == None

def test__takeover(agent):
    result = agent._takeover(store=None)
    assert result == None

def test_handoff(agent):
    result = agent.handoff(store=None)
    assert result == None

def test__handoff(agent):
    result = agent._handoff(store=None)
    assert result == None

def test_call(agent):
    agent_iter = agent(store=None)
    assert isinstance(agent_iter, GeneratorType)

def test_iter(agent):
    agent_iter = agent(store=None)
    result = agent_iter.__next__()
    assert result == ()
    with pytest.raises(StopIteration):
        agent_iter.__next__()

def test_rshift(agent):
    successor = BaseAgent(meta=BaseMeta(**{ "name": "successor_agent" }))
    agent >> successor # type: ignore
    assert "successor_agent" in agent.successors
    assert id(agent.successors["successor_agent"]) == id(successor)
