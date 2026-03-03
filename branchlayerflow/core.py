# -*- coding: utf-8 -*-

from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Generator, AsyncGenerator, Tuple, Optional, Dict, Any
import asyncio

class BaseMeta(BaseModel):
    name: str
    model_config = ConfigDict(frozen=True, extra="allow", validate_assignment=False, arbitrary_types_allowed=True)

class BaseAgent():
    def __init__(self, meta: BaseMeta) -> None:
        self._meta: BaseMeta = meta
        self.successors: Dict[str, BaseAgent] = {}
        self.parent_flow: Optional[BaseFlow] = None

    @property
    def meta(self) -> BaseMeta:
        return self._meta
  
    def takeover(self, store: Any) -> None:
        pass

    def _takeover(self, store: Any) -> None:
        return self.takeover(store)

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        pass

    def _handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return self.handoff(store)
  
    def __rshift__(self, successor: BaseAgent) -> BaseAgent:
        self.successors[successor.meta.name] = successor
        return successor
  
    def _iter(self, store: Any) -> Generator[Tuple[BaseAgent, ...]]:
        self._takeover(store)
        yield self._handoff(store) or ()

    def __call__(self, store: Any) -> Generator[Tuple[BaseAgent, ...]]:
        for successors in self._iter(store):
            yield successors

class BaseFlow(BaseAgent):
    def __init__(self, meta: BaseMeta, branches: Tuple[BaseAgent, ...]) -> None:
        super().__init__(meta)
        self._branches: Tuple[BaseAgent, ...] = branches
        self.n_branches: int = len(self.branches)

        for agent in self.branches:
            agent.parent_flow = self

    @property
    def branches(self) -> Tuple[BaseAgent, ...]:
        return self._branches

    def _get_successors(self, store: Any, agent: BaseAgent) -> Tuple[BaseAgent, ...]:
        assert agent != agent.parent_flow
        agent_iter: Generator[Tuple[BaseAgent, ...]] = agent(store)
        successors: Tuple[BaseAgent, ...] = agent_iter.__next__()
        agent_iter.close()

        flow = agent if isinstance(agent, BaseFlow) else agent.parent_flow
        assert flow is not None
        if isinstance(agent, BaseFlow):
            flow.n_branches = len(successors)
        else:
            flow.n_branches += len(successors) - 1

        while not successors and flow.n_branches <= 0 and flow.parent_flow:
            successors = flow._handoff(store) or ()
            flow = flow.parent_flow
            flow.n_branches += len(successors) - 1

        for successor in successors:
            if not isinstance(successor, BaseFlow) or (isinstance(successor, BaseFlow) and (successor.n_branches <= 0 or successor.parent_flow is None)):
                successor.parent_flow = flow

        return successors

    def _next_layer_successors(self, store: Any, layer_successors: Tuple[BaseAgent, ...]) -> Tuple[BaseAgent, ...]:
        successors = [self._get_successors(store, agent) for agent in layer_successors]
        return sum(successors, ())

    def _iter(self, store: Any) -> Generator[Tuple[BaseAgent, ...]]:
        self._takeover(store)
        layer_successors: Tuple[BaseAgent, ...] = self.branches
        yield layer_successors
        while layer_successors:
            layer_successors = self._next_layer_successors(store, layer_successors)
            if layer_successors:
                yield layer_successors
        yield self._handoff(store) or ()

class AsyncBaseAgent():
    def __init__(self, meta: BaseMeta) -> None:
        self._meta: BaseMeta = meta
        self.successors: Dict[str, AsyncBaseAgent] = {}
        self.parent_flow: Optional[AsyncBaseFlow] = None

    @property
    def meta(self) -> BaseMeta:
        return self._meta

    async def takeover(self, store: Any) -> None:
        pass

    async def _takeover(self, store: Any) -> None:
        return await self.takeover(store)

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        pass

    async def _handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return await self.handoff(store)

    def __rshift__(self, successor: AsyncBaseAgent) -> AsyncBaseAgent:
        self.successors[successor.meta.name] = successor
        return successor
  
    async def _iter(self, store: Any) -> AsyncGenerator[Tuple[AsyncBaseAgent, ...]]:
        await self._takeover(store)
        yield await self._handoff(store) or ()

    async def __call__(self, store: Any) -> AsyncGenerator[Tuple[AsyncBaseAgent, ...]]:
        async for successors in self._iter(store):
            yield successors

class AsyncBaseFlow(AsyncBaseAgent):
    def __init__(self, meta: BaseMeta, branches: Tuple[AsyncBaseAgent, ...]) -> None:
        super().__init__(meta)
        self._branches: Tuple[AsyncBaseAgent, ...] = branches
        self.n_branches: int = len(self.branches)

        for agent in self.branches:
            agent.parent_flow = self

    @property
    def branches(self) -> Tuple[AsyncBaseAgent, ...]:
        return self._branches

    async def _get_successors(self, store: Any, agent: AsyncBaseAgent) -> Tuple[AsyncBaseAgent, ...]:
        assert agent != agent.parent_flow
        agent_iter: AsyncGenerator[Tuple[AsyncBaseAgent, ...]] = agent(store)
        successors: Tuple[AsyncBaseAgent, ...] = await agent_iter.__anext__()
        await agent_iter.aclose()

        flow = agent if isinstance(agent, AsyncBaseFlow) else agent.parent_flow
        assert flow is not None
        if isinstance(agent, AsyncBaseFlow):
            flow.n_branches = len(successors)
        else:
            flow.n_branches += len(successors) - 1

        while not successors and flow.n_branches <= 0 and flow.parent_flow:
            successors = await flow._handoff(store) or ()
            flow = flow.parent_flow
            flow.n_branches += len(successors) - 1

        for successor in successors:
            if not isinstance(successor, AsyncBaseFlow) or (isinstance(successor, AsyncBaseFlow) and (successor.n_branches <= 0 or successor.parent_flow is None)):
                successor.parent_flow = flow

        return successors

    async def _next_layer_successors(self, store: Any, layer_successors: Tuple[AsyncBaseAgent, ...]) -> Tuple[AsyncBaseAgent, ...]:
        next_layer_successors = [await self._get_successors(store, agent) for agent in layer_successors]
        return sum(next_layer_successors, ())

    async def _iter(self, store: Any) -> AsyncGenerator[Tuple[AsyncBaseAgent, ...]]:
        await self._takeover(store)
        layer_successors: Tuple[AsyncBaseAgent, ...] = self.branches
        yield layer_successors
        while layer_successors:
            layer_successors = await self._next_layer_successors(store, layer_successors)
            if layer_successors:
                yield layer_successors
        yield await self._handoff(store) or ()

class AsyncParallelBaseFlow(AsyncBaseFlow):
    async def _next_layer_successors(self, store: Any, layer_successors: Tuple[AsyncBaseAgent, ...]) -> Tuple[AsyncBaseAgent, ...]:
        next_layer_successors = await asyncio.gather(*(self._get_successors(store, agent) for agent in layer_successors))
        return sum(next_layer_successors, ())
