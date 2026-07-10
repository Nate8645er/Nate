"""A minimal typed state-graph executor for agent workflows.

The execution model mirrors LangGraph (nodes transform a shared state dict,
edges select the next node, conditional edges branch on state) without the
dependency; if ``langgraph`` is installed, :func:`to_langgraph` converts a
graph so users can run it inside the LangChain ecosystem instead.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from jarvis.core.errors import AgentError
from jarvis.core.logging import get_logger

logger = get_logger("agents.graph")

State = dict[str, Any]
NodeFn = Callable[[State], Awaitable[State] | State]
RouterFn = Callable[[State], str]

END = "__end__"


class AgentGraph:
    """Directed graph of state-transforming nodes."""

    def __init__(self, name: str = "graph", max_steps: int = 50) -> None:
        self.name = name
        self.max_steps = max_steps
        self._nodes: dict[str, NodeFn] = {}
        self._edges: dict[str, str] = {}
        self._branches: dict[str, RouterFn] = {}
        self._entry: str | None = None

    def add_node(self, name: str, fn: NodeFn) -> AgentGraph:
        if name in (END,):
            raise AgentError(f"'{END}' is reserved")
        self._nodes[name] = fn
        if self._entry is None:
            self._entry = name
        return self

    def set_entry(self, name: str) -> AgentGraph:
        self._entry = name
        return self

    def add_edge(self, source: str, target: str) -> AgentGraph:
        self._edges[source] = target
        return self

    def add_conditional_edge(self, source: str, router: RouterFn) -> AgentGraph:
        """Router returns the next node name or :data:`END`."""
        self._branches[source] = router
        return self

    def _next(self, current: str, state: State) -> str:
        if current in self._branches:
            return self._branches[current](state)
        return self._edges.get(current, END)

    async def run(self, state: State | None = None) -> State:
        """Execute the graph until END, returning the final state."""
        if self._entry is None:
            raise AgentError(f"Graph '{self.name}' has no nodes")
        state = dict(state or {})
        current = self._entry
        for _ in range(self.max_steps):
            if current == END:
                return state
            node = self._nodes.get(current)
            if node is None:
                raise AgentError(f"Graph '{self.name}' has no node '{current}'")
            logger.debug("Graph %s: entering node %s", self.name, current)
            outcome = node(state)
            if inspect.isawaitable(outcome):
                outcome = await outcome
            if isinstance(outcome, dict):
                state.update(outcome)
            current = self._next(current, state)
        raise AgentError(f"Graph '{self.name}' exceeded {self.max_steps} steps")


def to_langgraph(graph: AgentGraph) -> Any:
    """Convert to a compiled LangGraph ``StateGraph`` (requires ``langgraph``)."""
    try:
        from langgraph.graph import END as LG_END
        from langgraph.graph import StateGraph
    except ImportError as exc:
        raise AgentError(
            "langgraph is not installed; install the 'langchain' extra"
        ) from exc

    builder = StateGraph(dict)
    for name, fn in graph._nodes.items():
        builder.add_node(name, fn)
    if graph._entry:
        builder.set_entry_point(graph._entry)
    for source, target in graph._edges.items():
        if target == END:
            builder.add_edge(source, LG_END)
        else:
            builder.add_edge(source, target)
    for source, router in graph._branches.items():
        builder.add_conditional_edges(
            source, lambda state, r=router: LG_END if r(state) == END else r(state)
        )
    return builder.compile()
