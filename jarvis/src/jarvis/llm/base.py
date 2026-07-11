"""Provider-agnostic chat model interface.

All providers implement :class:`LLMProvider`. The message/tool schema is a
neutral superset that each provider maps to its wire format, so agents and
tools never depend on a specific vendor.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ImageContent(BaseModel):
    """Base64-encoded image attached to a message (for vision models)."""

    media_type: str = "image/png"
    data_base64: str


class ToolCall(BaseModel):
    """A tool invocation requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_json_arguments(cls, call_id: str, name: str, arguments: str) -> ToolCall:
        try:
            parsed = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            parsed = {"_raw": arguments}
        if not isinstance(parsed, dict):
            parsed = {"value": parsed}
        return cls(id=call_id, name=name, arguments=parsed)


class Message(BaseModel):
    """One conversation turn."""

    role: Role
    content: str = ""
    images: list[ImageContent] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None  # set on Role.TOOL results
    name: str | None = None

    @classmethod
    def system(cls, content: str) -> Message:
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str, images: list[ImageContent] | None = None) -> Message:
        return cls(role=Role.USER, content=content, images=images or [])

    @classmethod
    def assistant(cls, content: str, tool_calls: list[ToolCall] | None = None) -> Message:
        return cls(role=Role.ASSISTANT, content=content, tool_calls=tool_calls or [])

    @classmethod
    def tool_result(cls, tool_call_id: str, name: str, content: str) -> Message:
        return cls(role=Role.TOOL, content=content, tool_call_id=tool_call_id, name=name)


class ToolSpec(BaseModel):
    """Declarative description of a callable tool exposed to the model."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class ChatResponse(BaseModel):
    """Final, non-streaming result of a chat call."""

    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    model: str = ""
    provider: str = ""
    finish_reason: str = "stop"
    usage: Usage = Field(default_factory=Usage)


class StreamChunk(BaseModel):
    """Incremental streaming event.

    ``delta`` carries text as it is generated. When the model requests tools,
    the final chunk has ``done=True`` and carries the accumulated
    ``tool_calls`` plus the full ``response``.
    """

    delta: str = ""
    done: bool = False
    response: ChatResponse | None = None


class ModelInfo(BaseModel):
    """Capability card used by the router for automatic model selection."""

    name: str
    provider: str
    context_window: int = 128_000
    supports_tools: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_tier: int = 1  # 0=free/local, 1=cheap, 2=mid, 3=premium
    quality: int = 5  # 1..10 rough quality score used for ranking
    local: bool = False


class ChatOptions(BaseModel):
    """Per-call generation options."""

    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    stop: list[str] = Field(default_factory=list)
    json_mode: bool = False


class LLMProvider(ABC):
    """Interface every chat-model backend implements."""

    name: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
    ) -> ChatResponse:
        """Run a full (non-streaming) chat completion."""

    @abstractmethod
    def chat_stream(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion as :class:`StreamChunk` events."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return models this provider can serve right now."""

    async def health_check(self) -> bool:
        """Cheap availability probe; default checks :meth:`list_models`."""
        try:
            await self.list_models()
            return True
        except Exception:
            return False

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        """Return embedding vectors. Providers without embeddings raise."""
        raise NotImplementedError(f"Provider '{self.name}' does not support embeddings")

    async def aclose(self) -> None:
        """Release network resources."""
