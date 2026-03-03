from typing import Any, Tuple, Optional
from branchlayerflow import BaseMeta, BaseAgent
from types import GeneratorType
import pytest


successor_agent = BaseAgent(meta=BaseMeta(**{ "name": "successor_agent" }))
store = { "x": 1 }

class Agent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["x"] += 1

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        store["x"] += 1
        return successor_agent,

@pytest.fixture
def agent():
    return Agent(meta=BaseMeta(**{ "name": "agent" }))

def test_iter(agent):
    agent_iter = agent(store=store)
    assert isinstance(agent_iter, GeneratorType)
    result = agent_iter.__next__()
    assert result == (successor_agent,)
    with pytest.raises(StopIteration):
        agent_iter.__next__()

def test_store_result():
    assert store["x"] == 3
