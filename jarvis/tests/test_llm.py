"""Tests for the LLM layer: wire formats, streaming, registry and router."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from pydantic import SecretStr

from jarvis.core.config import JarvisConfig, ProviderConfig
from jarvis.core.errors import ProviderUnavailableError
from jarvis.llm.base import (
    ChatOptions,
    ChatResponse,
    ImageContent,
    LLMProvider,
    Message,
    ModelInfo,
    StreamChunk,
    ToolCall,
    ToolSpec,
)
from jarvis.llm.providers.anthropic import AnthropicProvider
from jarvis.llm.providers.openai import OpenAIProvider
from jarvis.llm.registry import ProviderRegistry, register_provider
from jarvis.llm.router import ModelRouter, TaskRequirements


def _openai_provider() -> OpenAIProvider:
    return OpenAIProvider(ProviderConfig(api_key=SecretStr("sk-test")))


class TestToolCall:
    def test_from_json_arguments(self) -> None:
        call = ToolCall.from_json_arguments("1", "add", '{"a": 1, "b": 2}')
        assert call.arguments == {"a": 1, "b": 2}

    def test_from_invalid_json(self) -> None:
        call = ToolCall.from_json_arguments("1", "add", "not-json")
        assert call.arguments == {"_raw": "not-json"}


class TestOpenAICompat:
    @respx.mock
    async def test_chat_roundtrip(self) -> None:
        provider = _openai_provider()
        route = respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "gpt-4o",
                    "choices": [
                        {
                            "message": {"content": "Hello Sir."},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 3},
                },
            )
        )
        response = await provider.chat(
            [Message.system("You are JARVIS"), Message.user("Hi")],
            options=ChatOptions(model="gpt-4o", temperature=0.1),
        )
        assert response.content == "Hello Sir."
        assert response.usage.input_tokens == 10
        payload = json.loads(route.calls[0].request.content)
        assert payload["model"] == "gpt-4o"
        assert payload["messages"][0] == {"role": "system", "content": "You are JARVIS"}
        await provider.aclose()

    @respx.mock
    async def test_tool_calls_parsed(self) -> None:
        provider = _openai_provider()
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {
                                            "name": "get_weather",
                                            "arguments": '{"city": "Zurich"}',
                                        },
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ]
                },
            )
        )
        tools = [ToolSpec(name="get_weather", description="d")]
        response = await provider.chat([Message.user("weather?")], tools=tools)
        assert response.tool_calls[0].name == "get_weather"
        assert response.tool_calls[0].arguments == {"city": "Zurich"}
        await provider.aclose()

    @respx.mock
    async def test_streaming(self) -> None:
        provider = _openai_provider()
        sse = (
            'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"lo"},"finish_reason":"stop"}]}\n\n'
            "data: [DONE]\n\n"
        )
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200, content=sse.encode(), headers={"content-type": "text/event-stream"}
            )
        )
        deltas: list[str] = []
        final: ChatResponse | None = None
        async for chunk in provider.chat_stream([Message.user("hi")]):
            if chunk.done:
                final = chunk.response
            else:
                deltas.append(chunk.delta)
        assert "".join(deltas) == "Hello"
        assert final is not None and final.content == "Hello"
        await provider.aclose()

    @respx.mock
    async def test_http_error_raises(self) -> None:
        provider = _openai_provider()
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(429, json={"error": "rate limited"})
        )
        from jarvis.core.errors import ProviderError

        with pytest.raises(ProviderError) as excinfo:
            await provider.chat([Message.user("hi")])
        assert excinfo.value.status_code == 429
        await provider.aclose()

    def test_image_message_wire_format(self) -> None:
        provider = _openai_provider()
        wire = provider._to_wire_messages(
            [Message.user("what is this?", images=[ImageContent(data_base64="QUJD")])]
        )
        parts = wire[0]["content"]
        assert parts[0]["type"] == "text"
        assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,QUJD")


class TestAnthropic:
    @respx.mock
    async def test_chat_and_system_split(self) -> None:
        provider = AnthropicProvider(ProviderConfig(api_key=SecretStr("sk-ant")))
        route = respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "claude-sonnet-4-5",
                    "content": [{"type": "text", "text": "At your service."}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 5, "output_tokens": 4},
                },
            )
        )
        response = await provider.chat(
            [Message.system("You are JARVIS"), Message.user("Status?")]
        )
        assert response.content == "At your service."
        payload = json.loads(route.calls[0].request.content)
        assert payload["system"] == "You are JARVIS"
        assert payload["messages"][0]["role"] == "user"
        await provider.aclose()

    @respx.mock
    async def test_tool_use_parsed(self) -> None:
        provider = AnthropicProvider(ProviderConfig(api_key=SecretStr("sk-ant")))
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(
                200,
                json={
                    "content": [
                        {"type": "tool_use", "id": "tu_1", "name": "search", "input": {"q": "x"}}
                    ],
                    "stop_reason": "tool_use",
                },
            )
        )
        response = await provider.chat(
            [Message.user("find x")], tools=[ToolSpec(name="search", description="d")]
        )
        assert response.tool_calls[0].id == "tu_1"
        assert response.tool_calls[0].arguments == {"q": "x"}
        await provider.aclose()


class _FakeProvider(LLMProvider):
    """In-memory provider used for router tests."""

    name = "fake"

    def __init__(self, models: list[ModelInfo], reply: str = "ok") -> None:
        self._models = models
        self._reply = reply
        self.last_options: ChatOptions | None = None

    async def chat(self, messages, *, tools=None, options=None) -> ChatResponse:
        self.last_options = options
        return ChatResponse(content=self._reply, model=options.model if options else "")

    async def chat_stream(self, messages, *, tools=None, options=None):
        yield StreamChunk(delta=self._reply)
        yield StreamChunk(done=True, response=ChatResponse(content=self._reply))

    async def list_models(self) -> list[ModelInfo]:
        return self._models


class TestRouter:
    def _registry_with_fake(self, config: JarvisConfig, models: list[ModelInfo]):
        fake = _FakeProvider(models)

        class FakeType:
            def __new__(cls, provider_config):
                return fake

        register_provider("fake", FakeType)  # type: ignore[arg-type]
        registry = ProviderRegistry(config)
        registry._health = {name: name == "fake" for name in registry.available_names}
        return registry, fake

    async def test_auto_selects_best_quality(self, config: JarvisConfig) -> None:
        models = [
            ModelInfo(name="small", provider="fake", quality=4, cost_tier=0),
            ModelInfo(name="big", provider="fake", quality=9, cost_tier=2),
        ]
        registry, _ = self._registry_with_fake(config, models)
        router = ModelRouter(config, registry)
        routed = await router.select(TaskRequirements())
        assert routed.model.name == "big"

    async def test_vision_requirement_filters(self, config: JarvisConfig) -> None:
        models = [
            ModelInfo(name="text-only", provider="fake", quality=9, supports_vision=False),
            ModelInfo(name="eyes", provider="fake", quality=5, supports_vision=True),
        ]
        registry, _ = self._registry_with_fake(config, models)
        router = ModelRouter(config, registry)
        routed = await router.select(TaskRequirements(needs_vision=True))
        assert routed.model.name == "eyes"

    async def test_prefer_local(self, config: JarvisConfig) -> None:
        config.llm.prefer_local = True
        models = [
            ModelInfo(name="cloud", provider="fake", quality=9, cost_tier=2),
            ModelInfo(name="local", provider="fake", quality=6, cost_tier=0, local=True),
        ]
        registry, _ = self._registry_with_fake(config, models)
        router = ModelRouter(config, registry)
        routed = await router.select(TaskRequirements())
        assert routed.model.name == "local"

    async def test_no_provider_raises(self, config: JarvisConfig) -> None:
        registry = ProviderRegistry(config)
        registry._health = dict.fromkeys(registry.available_names, False)
        router = ModelRouter(config, registry)
        with pytest.raises(ProviderUnavailableError):
            await router.select(TaskRequirements())

    async def test_chat_fills_defaults(self, config: JarvisConfig) -> None:
        models = [ModelInfo(name="m", provider="fake", quality=5)]
        registry, fake = self._registry_with_fake(config, models)
        router = ModelRouter(config, registry)
        response = await router.chat([Message.user("hi")])
        assert response.content == "ok"
        assert fake.last_options is not None
        assert fake.last_options.model == "m"
        assert fake.last_options.max_tokens == config.llm.max_tokens
