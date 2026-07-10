"""Anthropic Claude provider using the public Messages API over httpx."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from jarvis.core.config import ProviderConfig
from jarvis.core.errors import ProviderError, ProviderUnavailableError
from jarvis.llm.base import (
    ChatOptions,
    ChatResponse,
    LLMProvider,
    Message,
    ModelInfo,
    Role,
    StreamChunk,
    ToolCall,
    ToolSpec,
    Usage,
)

_API_VERSION = "2023-06-01"


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    default_base_url = "https://api.anthropic.com"
    default_model = "claude-sonnet-4-5"
    model_catalog = [
        ModelInfo(name="claude-opus-4-8", provider="anthropic", context_window=200_000, supports_vision=True, cost_tier=3, quality=10),
        ModelInfo(name="claude-sonnet-4-5", provider="anthropic", context_window=200_000, supports_vision=True, cost_tier=2, quality=9),
        ModelInfo(name="claude-haiku-4-5", provider="anthropic", context_window=200_000, supports_vision=True, cost_tier=1, quality=7),
    ]

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self.base_url = (config.base_url or self.default_base_url).rstrip("/")
        api_key = config.api_key.get_secret_value() if config.api_key else ""
        self._has_key = bool(api_key)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": _API_VERSION,
                "Content-Type": "application/json",
                **config.extra_headers,
            },
            timeout=config.timeout_seconds,
        )

    # -- mapping ---------------------------------------------------------------

    def _to_wire(self, messages: list[Message]) -> tuple[str, list[dict[str, Any]]]:
        """Split system prompt and convert turns to Anthropic content blocks."""
        system_parts: list[str] = []
        wire: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role is Role.SYSTEM:
                system_parts.append(msg.content)
                continue
            if msg.role is Role.TOOL:
                wire.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id or "",
                                "content": msg.content,
                            }
                        ],
                    }
                )
                continue
            blocks: list[dict[str, Any]] = []
            if msg.content:
                blocks.append({"type": "text", "text": msg.content})
            for img in msg.images:
                blocks.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": img.media_type,
                            "data": img.data_base64,
                        },
                    }
                )
            for call in msg.tool_calls:
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": call.id,
                        "name": call.name,
                        "input": call.arguments,
                    }
                )
            wire.append({"role": msg.role.value, "content": blocks or [{"type": "text", "text": ""}]})
        return "\n\n".join(system_parts), wire

    def _build_payload(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None,
        options: ChatOptions | None,
        stream: bool,
    ) -> dict[str, Any]:
        opts = options or ChatOptions()
        system, wire = self._to_wire(messages)
        payload: dict[str, Any] = {
            "model": opts.model or self._config.default_model or self.default_model,
            "messages": wire,
            "max_tokens": opts.max_tokens or 4096,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if opts.temperature is not None:
            payload["temperature"] = opts.temperature
        if opts.stop:
            payload["stop_sequences"] = opts.stop
        if tools:
            payload["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": t.parameters}
                for t in tools
            ]
        return payload

    @staticmethod
    def _parse_body(body: dict[str, Any]) -> ChatResponse:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in body.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id", ""),
                        name=block.get("name", ""),
                        arguments=block.get("input") or {},
                    )
                )
        usage = body.get("usage") or {}
        return ChatResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            model=body.get("model", ""),
            provider="anthropic",
            finish_reason=body.get("stop_reason") or "stop",
            usage=Usage(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            ),
        )

    # -- LLMProvider -------------------------------------------------------------

    async def chat(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
    ) -> ChatResponse:
        payload = self._build_payload(messages, tools, options, stream=False)
        try:
            response = await self._client.post("/v1/messages", json=payload)
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError("Cannot reach Anthropic API", provider=self.name, cause=exc) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc), provider=self.name, cause=exc) from exc
        if response.status_code >= 400:
            raise ProviderError(
                f"Anthropic returned HTTP {response.status_code}: {response.text[:500]}",
                provider=self.name,
                status_code=response.status_code,
            )
        return self._parse_body(response.json())

    async def chat_stream(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
    ) -> AsyncIterator[StreamChunk]:
        payload = self._build_payload(messages, tools, options, stream=True)
        text_parts: list[str] = []
        tool_blocks: dict[int, dict[str, Any]] = {}
        finish_reason = "stop"
        model = payload["model"]
        usage = Usage()
        try:
            async with self._client.stream("POST", "/v1/messages", json=payload) as resp:
                if resp.status_code >= 400:
                    text = (await resp.aread()).decode("utf-8", "replace")
                    raise ProviderError(
                        f"Anthropic returned HTTP {resp.status_code}: {text[:500]}",
                        provider=self.name,
                        status_code=resp.status_code,
                    )
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    etype = event.get("type")
                    if etype == "message_start":
                        model = event.get("message", {}).get("model", model)
                    elif etype == "content_block_start":
                        block = event.get("content_block", {})
                        if block.get("type") == "tool_use":
                            tool_blocks[event.get("index", 0)] = {
                                "id": block.get("id", ""),
                                "name": block.get("name", ""),
                                "json": "",
                            }
                    elif etype == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            piece = delta.get("text", "")
                            text_parts.append(piece)
                            yield StreamChunk(delta=piece)
                        elif delta.get("type") == "input_json_delta":
                            idx = event.get("index", 0)
                            if idx in tool_blocks:
                                tool_blocks[idx]["json"] += delta.get("partial_json", "")
                    elif etype == "message_delta":
                        finish_reason = event.get("delta", {}).get("stop_reason") or finish_reason
                        usage.output_tokens = event.get("usage", {}).get(
                            "output_tokens", usage.output_tokens
                        )
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError("Cannot reach Anthropic API", provider=self.name, cause=exc) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc), provider=self.name, cause=exc) from exc

        tool_calls = [
            ToolCall.from_json_arguments(
                call_call_id=slot["id"] or f"call_{idx}", name=slot["name"], arguments=slot["json"] or "{}"
            )
            for idx, slot in sorted(tool_blocks.items())
        ]
        final = ChatResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            model=model,
            provider=self.name,
            finish_reason=finish_reason,
            usage=usage,
        )
        yield StreamChunk(done=True, response=final)

    async def list_models(self) -> list[ModelInfo]:
        if not self._has_key:
            raise ProviderUnavailableError("Anthropic API key not configured", provider=self.name)
        response = await self._client.get("/v1/models")
        if response.status_code >= 400:
            raise ProviderUnavailableError(
                f"Anthropic /v1/models returned HTTP {response.status_code}", provider=self.name
            )
        catalog = {info.name: info for info in self.model_catalog}
        models = []
        for item in response.json().get("data", []):
            model_id = item.get("id", "")
            models.append(
                catalog.get(model_id)
                or ModelInfo(
                    name=model_id,
                    provider=self.name,
                    context_window=200_000,
                    supports_vision=True,
                    cost_tier=2,
                    quality=8,
                )
            )
        return models

    async def health_check(self) -> bool:
        return self._has_key and await super().health_check()

    async def aclose(self) -> None:
        await self._client.aclose()
