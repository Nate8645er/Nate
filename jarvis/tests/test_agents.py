"""Tests for the agent framework: tools, base loop, graph, orchestrator."""

from __future__ import annotations

import pytest

from jarvis.agents.base import AgentResult, BaseAgent
from jarvis.agents.graph import END, AgentGraph
from jarvis.agents.orchestrator import AgentOrchestrator, _extract_json
from jarvis.agents.tools import ToolRegistry
from jarvis.core.config import JarvisConfig
from jarvis.core.errors import AgentError
from jarvis.core.events import EventBus
from jarvis.core.security import PermissionManager
from jarvis.llm.base import ChatResponse, Message, StreamChunk, ToolCall


class ScriptedRouter:
    """Router stub returning queued responses."""

    def __init__(self, responses: list[ChatResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[list[Message]] = []

    async def chat(self, messages, *, tools=None, options=None, requirements=None) -> ChatResponse:
        self.calls.append(list(messages))
        return self._responses.pop(0)

    async def chat_stream(self, messages, *, tools=None, options=None, requirements=None):
        response = self._responses.pop(0)
        for i in range(0, len(response.content), 4):
            yield StreamChunk(delta=response.content[i : i + 4])
        yield StreamChunk(done=True, response=response)


class TestToolRegistry:
    async def test_register_execute(self) -> None:
        registry = ToolRegistry()

        async def add(a: int, b: int) -> int:
            return a + b

        registry.register_function("add", "adds", add, tags={"math"})
        assert await registry.execute("add", {"a": 2, "b": 3}) == "5"

    async def test_sync_handler_runs_in_thread(self) -> None:
        registry = ToolRegistry()
        registry.register_function("greet", "greets", lambda name: f"Hi {name}")
        assert await registry.execute("greet", {"name": "Nate"}) == "Hi Nate"

    async def test_unknown_tool_and_bad_args(self) -> None:
        registry = ToolRegistry()
        registry.register_function("noop", "d", lambda: "ok")
        assert "unknown tool" in await registry.execute("nope", {})
        assert "invalid arguments" in await registry.execute("noop", {"x": 1})

    async def test_capability_denied(self, config: JarvisConfig) -> None:
        permissions = PermissionManager(config)
        registry = ToolRegistry(permissions)
        registry.register_function("rm", "d", lambda: "gone", capability="files.delete")
        result = await registry.execute("rm", {})
        assert result.startswith("Permission denied")

    async def test_tag_filter_and_source_unregister(self) -> None:
        registry = ToolRegistry()
        registry.register_function("a", "d", lambda: 1, tags={"x"}, source="p1")
        registry.register_function("b", "d", lambda: 2, tags={"y"}, source="p1")
        assert {t.name for t in registry.by_tags({"x"})} == {"a"}
        assert registry.unregister_source("p1") == 2
        assert registry.all() == []

    async def test_error_result_is_string(self) -> None:
        registry = ToolRegistry()

        def boom() -> None:
            raise ValueError("kaputt")

        registry.register_function("boom", "d", boom)
        result = await registry.execute("boom", {})
        assert "ValueError" in result and "kaputt" in result


class TestBaseAgent:
    async def test_tool_loop(self) -> None:
        registry = ToolRegistry()
        registry.register_function("lookup", "d", lambda q: f"result-for-{q}", tags={"search"})
        router = ScriptedRouter(
            [
                ChatResponse(
                    content="",
                    tool_calls=[ToolCall(id="1", name="lookup", arguments={"q": "x"})],
                ),
                ChatResponse(content="The answer is result-for-x."),
            ]
        )
        agent = BaseAgent(router, registry, EventBus(), name="t", tool_tags={"search"})
        result = await agent.run("find x")
        assert result.success
        assert "result-for-x" in result.output
        # Second call must contain the tool result message.
        assert any(m.role.value == "tool" for m in router.calls[1])

    async def test_max_iterations(self) -> None:
        registry = ToolRegistry()
        registry.register_function("loop", "d", lambda: "again", tags={"x"})
        responses = [
            ChatResponse(content="", tool_calls=[ToolCall(id=str(i), name="loop", arguments={})])
            for i in range(20)
        ]
        router = ScriptedRouter(responses)
        agent = BaseAgent(router, registry, name="t", tool_tags={"x"})
        agent.max_iterations = 3
        result = await agent.run("go")
        assert not result.success

    async def test_run_stream_yields_deltas(self) -> None:
        router = ScriptedRouter([ChatResponse(content="Hello Sir")])
        agent = BaseAgent(router, ToolRegistry(), name="t", tool_tags=set())
        deltas: list[str] = []
        final: AgentResult | None = None
        async for item in agent.run_stream("hi"):
            if isinstance(item, AgentResult):
                final = item
            else:
                deltas.append(item)
        assert "".join(deltas) == "Hello Sir"
        assert final is not None and final.output == "Hello Sir"


class TestAgentGraph:
    async def test_linear_and_conditional(self) -> None:
        graph = AgentGraph()
        graph.add_node("a", lambda s: {"x": s.get("x", 0) + 1})
        graph.add_node("b", lambda s: {"x": s["x"] * 10})
        graph.add_edge("a", "b")
        graph.add_conditional_edge("b", lambda s: END if s["x"] >= 10 else "a")
        state = await graph.run()
        assert state["x"] == 10

    async def test_max_steps_guard(self) -> None:
        graph = AgentGraph(max_steps=5)
        graph.add_node("a", lambda s: s)
        graph.add_edge("a", "a")
        with pytest.raises(AgentError):
            await graph.run()


class TestOrchestrator:
    def test_extract_json_variants(self) -> None:
        assert _extract_json('{"steps": []}') == {"steps": []}
        assert _extract_json('prose\n```json\n{"a": 1}\n```\nmore') == {"a": 1}
        assert _extract_json("no json here") == {}

    async def test_plan_execute_synthesise(self) -> None:
        registry = ToolRegistry()
        plan = (
            '{"steps": [{"agent": "research", "task": "find it"}], "direct_answer": ""}'
        )
        router = ScriptedRouter(
            [
                ChatResponse(content=plan),  # planner
                ChatResponse(content="Found: 42."),  # research agent
            ]
        )
        orchestrator = AgentOrchestrator(router, EventBus())
        orchestrator.register(BaseAgent(router, registry, name="planner", tool_tags=set()))
        orchestrator.register(BaseAgent(router, registry, name="research", tool_tags=set()))
        result = await orchestrator.run("what is the answer?")
        assert result.success
        assert "42" in result.output

    async def test_direct_answer_short_circuit(self) -> None:
        router = ScriptedRouter(
            [ChatResponse(content='{"steps": [], "direct_answer": "It is 42."}')]
        )
        orchestrator = AgentOrchestrator(router, EventBus())
        orchestrator.register(BaseAgent(router, ToolRegistry(), name="planner", tool_tags=set()))
        orchestrator.register(BaseAgent(router, ToolRegistry(), name="research", tool_tags=set()))
        result = await orchestrator.run("simple question")
        assert result.output == "It is 42."

    async def test_roster_management(self) -> None:
        router = ScriptedRouter([])
        orchestrator = AgentOrchestrator(router, EventBus())
        agent = BaseAgent(router, ToolRegistry(), name="x", description="dx")
        orchestrator.register(agent)
        assert orchestrator.roster() == {"x": "dx"}
        orchestrator.unregister("x")
        with pytest.raises(AgentError):
            orchestrator.get("x")
