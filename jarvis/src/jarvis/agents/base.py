"""BaseAgent: the tool-use loop every JARVIS agent is built on."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from jarvis.agents.tools import ToolRegistry
from jarvis.core.events import EventBus
from jarvis.core.logging import get_logger
from jarvis.llm.base import ChatOptions, ChatResponse, Message
from jarvis.llm.router import ModelRouter, TaskRequirements

logger = get_logger("agents.base")


@dataclass(slots=True)
class AgentStep:
    """One iteration of an agent run (for tracing/GUI display)."""

    kind: str  # "thought" | "tool_call" | "tool_result" | "answer"
    content: str = ""
    tool: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentResult:
    """Final outcome of an agent run."""

    output: str
    steps: list[AgentStep] = field(default_factory=list)
    success: bool = True


class BaseAgent:
    """A single agent: system prompt + a themed toolset + the model router.

    Subclasses (or plugin-defined instances) customise ``name``,
    ``description``, ``system_prompt``, ``tool_tags`` and ``requirements``.
    """

    name: str = "agent"
    description: str = "General-purpose agent"
    system_prompt: str = "You are a helpful assistant."
    tool_tags: set[str] | None = None  # None => all registered tools
    max_iterations: int = 12

    def __init__(
        self,
        router: ModelRouter,
        tools: ToolRegistry,
        events: EventBus | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        system_prompt: str | None = None,
        tool_tags: set[str] | None = None,
    ) -> None:
        self.router = router
        self.tools = tools
        self.events = events
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if tool_tags is not None:
            self.tool_tags = tool_tags

    def requirements(self) -> TaskRequirements:
        """Model requirements for this agent; subclasses tune this."""
        return TaskRequirements(needs_tools=bool(self.tools.by_tags(self.tool_tags)))

    def build_messages(self, task: str, context: str = "") -> list[Message]:
        system = self.system_prompt
        if context:
            system = f"{system}\n\n{context}"
        return [Message.system(system), Message.user(task)]

    async def _emit(self, topic: str, data: dict[str, Any]) -> None:
        if self.events is not None:
            await self.events.publish(topic, {"agent": self.name, **data})

    async def run(
        self,
        task: str,
        *,
        context: str = "",
        history: list[Message] | None = None,
        options: ChatOptions | None = None,
    ) -> AgentResult:
        """Run the agent loop until the model stops calling tools."""
        messages = self.build_messages(task, context)
        if history:
            # Insert prior conversation between system prompt and current task.
            messages = [messages[0], *history, *messages[1:]]
        steps: list[AgentStep] = []
        specs = self.tools.specs(self.tool_tags)

        for _ in range(self.max_iterations):
            response: ChatResponse = await self.router.chat(
                messages,
                tools=specs or None,
                options=options,
                requirements=self.requirements(),
            )
            if response.content:
                steps.append(AgentStep(kind="thought", content=response.content))
            if not response.tool_calls:
                await self._emit("agent.finished", {"output": response.content})
                return AgentResult(output=response.content, steps=steps)

            messages.append(
                Message.assistant(response.content, tool_calls=response.tool_calls)
            )
            for call in response.tool_calls:
                steps.append(
                    AgentStep(kind="tool_call", tool=call.name, arguments=call.arguments)
                )
                await self._emit("agent.tool_call", {"tool": call.name, "arguments": call.arguments})
                result = await self.tools.execute(call.name, call.arguments)
                steps.append(AgentStep(kind="tool_result", tool=call.name, content=result))
                await self._emit("agent.tool_result", {"tool": call.name, "result": result[:500]})
                messages.append(Message.tool_result(call.id, call.name, result))

        logger.warning("Agent '%s' hit max iterations (%d)", self.name, self.max_iterations)
        return AgentResult(
            output="I could not finish this task within the allowed number of steps.",
            steps=steps,
            success=False,
        )

    async def run_stream(
        self,
        task: str,
        *,
        context: str = "",
        history: list[Message] | None = None,
        options: ChatOptions | None = None,
    ) -> AsyncIterator[str | AgentResult]:
        """Like :meth:`run` but yields text deltas; the last item is the AgentResult."""
        messages = self.build_messages(task, context)
        if history:
            messages = [messages[0], *history, *messages[1:]]
        steps: list[AgentStep] = []
        specs = self.tools.specs(self.tool_tags)

        for _ in range(self.max_iterations):
            final: ChatResponse | None = None
            async for chunk in self.router.chat_stream(
                messages,
                tools=specs or None,
                options=options,
                requirements=self.requirements(),
            ):
                if chunk.delta:
                    yield chunk.delta
                if chunk.done:
                    final = chunk.response
            if final is None:
                break
            if final.content:
                steps.append(AgentStep(kind="thought", content=final.content))
            if not final.tool_calls:
                yield AgentResult(output=final.content, steps=steps)
                return
            messages.append(Message.assistant(final.content, tool_calls=final.tool_calls))
            for call in final.tool_calls:
                steps.append(AgentStep(kind="tool_call", tool=call.name, arguments=call.arguments))
                await self._emit("agent.tool_call", {"tool": call.name, "arguments": call.arguments})
                result = await self.tools.execute(call.name, call.arguments)
                steps.append(AgentStep(kind="tool_result", tool=call.name, content=result))
                messages.append(Message.tool_result(call.id, call.name, result))

        yield AgentResult(
            output="I could not finish this task within the allowed number of steps.",
            steps=steps,
            success=False,
        )
