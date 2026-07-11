"""OpenAI-compatible chat completions client over httpx.

This single implementation powers OpenAI itself plus every service that speaks
the same wire protocol: OpenRouter, DeepSeek, Mistral, Ollama, LM Studio and
arbitrary local/self-hosted endpoints. Subclasses only set connection details
and a model catalog.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from jarvis.core.config import ProviderConfig
from jarvis.core.errors import ProviderError, ProviderUnavailableError
from jarvis.core.logging import get_logger
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

logger = get_logger("llm.openai_compat")


class OpenAICompatProvider(LLMProvider):
    """Chat-completions client for any OpenAI-compatible API."""

    name = "openai-compat"
    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-4o-mini"
    embedding_model = "text-embedding-3-small"
    requires_api_key = True
    # Static capability hints; refined per subclass.
    model_catalog: list[ModelInfo] = []

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self.base_url = (config.base_url or self.default_base_url).rstrip("/")
        headers = {"Content-Type": "application/json", **config.extra_headers}
        api_key = config.api_key.get_secret_value() if config.api_key else None
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        elif self.requires_api_key:
            logger.debug("Provider %s has no API key configured", self.name)
        self._has_key = bool(api_key)
        self._client = httpx.AsyncClient(
            base_url=self.base_url, headers=headers, timeout=config.timeout_seconds
        )

    # -- request building ----------------------------------------------------

    def _to_wire_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        wire: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role is Role.TOOL:
                wire.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id or "",
                        "content": msg.content,
                    }
                )
                continue
            entry: dict[str, Any] = {"role": msg.role.value}
            if msg.images:
                parts: list[dict[str, Any]] = [{"type": "text", "text": msg.content}]
                parts.extend(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{img.media_type};base64,{img.data_base64}"},
                    }
                    for img in msg.images
                )
                entry["content"] = parts
            else:
                entry["content"] = msg.content
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments, ensure_ascii=False),
                        },
                    }
                    for call in msg.tool_calls
                ]
            wire.append(entry)
        return wire

    def _build_payload(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None,
        options: ChatOptions | None,
        stream: bool,
    ) -> dict[str, Any]:
        opts = options or ChatOptions()
        payload: dict[str, Any] = {
            "model": opts.model or self._config.default_model or self.default_model,
            "messages": self._to_wire_messages(messages),
            "stream": stream,
        }
        if opts.temperature is not None:
            payload["temperature"] = opts.temperature
        if opts.max_tokens is not None:
            payload["max_tokens"] = opts.max_tokens
        if opts.stop:
            payload["stop"] = opts.stop
        if opts.json_mode:
            payload["response_format"] = {"type": "json_object"}
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ]
        return payload

    async def _post(self, path: str, payload: dict[str, Any]) -> httpx.Response:
        try:
            response = await self._client.post(path, json=payload)
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                f"Cannot reach {self.name} at {self.base_url}", provider=self.name, cause=exc
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc), provider=self.name, cause=exc) from exc
        if response.status_code >= 400:
            raise ProviderError(
                f"{self.name} returned HTTP {response.status_code}: {response.text[:500]}",
                provider=self.name,
                status_code=response.status_code,
            )
        return response

    # -- LLMProvider ---------------------------------------------------------

    async def chat(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
    ) -> ChatResponse:
        payload = self._build_payload(messages, tools, options, stream=False)
        response = await self._post("/chat/completions", payload)
        body = response.json()
        return self._parse_response(body, payload["model"])

    def _parse_response(self, body: dict[str, Any], model: str) -> ChatResponse:
        choices = body.get("choices") or []
        if not choices:
            raise ProviderError(f"{self.name} returned no choices", provider=self.name)
        choice = choices[0]
        message = choice.get("message") or {}
        tool_calls = [
            ToolCall.from_json_arguments(
                call_id=call.get("id") or f"call_{i}",
                name=call.get("function", {}).get("name", ""),
                arguments=call.get("function", {}).get("arguments", "{}"),
            )
            for i, call in enumerate(message.get("tool_calls") or [])
        ]
        usage = body.get("usage") or {}
        return ChatResponse(
            content=message.get("content") or "",
            tool_calls=tool_calls,
            model=body.get("model", model),
            provider=self.name,
            finish_reason=choice.get("finish_reason") or "stop",
            usage=Usage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            ),
        )

    async def chat_stream(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
    ) -> AsyncIterator[StreamChunk]:
        payload = self._build_payload(messages, tools, options, stream=True)
        content_parts: list[str] = []
        finish_reason = "stop"
        model = payload["model"]
        # tool call deltas accumulate by index
        pending_calls: dict[int, dict[str, str]] = {}
        try:
            async with self._client.stream("POST", "/chat/completions", json=payload) as resp:
                if resp.status_code >= 400:
                    text = (await resp.aread()).decode("utf-8", "replace")
                    raise ProviderError(
                        f"{self.name} returned HTTP {resp.status_code}: {text[:500]}",
                        provider=self.name,
                        status_code=resp.status_code,
                    )
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    for choice in event.get("choices") or []:
                        if choice.get("finish_reason"):
                            finish_reason = choice["finish_reason"]
                        delta = choice.get("delta") or {}
                        piece = delta.get("content")
                        if piece:
                            content_parts.append(piece)
                            yield StreamChunk(delta=piece)
                        for call in delta.get("tool_calls") or []:
                            idx = call.get("index", 0)
                            slot = pending_calls.setdefault(
                                idx, {"id": "", "name": "", "arguments": ""}
                            )
                            if call.get("id"):
                                slot["id"] = call["id"]
                            fn = call.get("function") or {}
                            if fn.get("name"):
                                slot["name"] += fn["name"]
                            if fn.get("arguments"):
                                slot["arguments"] += fn["arguments"]
                    if event.get("model"):
                        model = event["model"]
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                f"Cannot reach {self.name} at {self.base_url}", provider=self.name, cause=exc
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc), provider=self.name, cause=exc) from exc

        tool_calls = [
            ToolCall.from_json_arguments(
                call_id=slot["id"] or f"call_{idx}", name=slot["name"], arguments=slot["arguments"]
            )
            for idx, slot in sorted(pending_calls.items())
        ]
        final = ChatResponse(
            content="".join(content_parts),
            tool_calls=tool_calls,
            model=model,
            provider=self.name,
            finish_reason=finish_reason,
        )
        yield StreamChunk(done=True, response=final)

    async def list_models(self) -> list[ModelInfo]:
        try:
            response = await self._client.get("/models")
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                f"Cannot list models for {self.name}", provider=self.name, cause=exc
            ) from exc
        if response.status_code >= 400:
            raise ProviderUnavailableError(
                f"{self.name} /models returned HTTP {response.status_code}", provider=self.name
            )
        catalog = {info.name: info for info in self.model_catalog}
        models: list[ModelInfo] = []
        for item in response.json().get("data", []):
            model_id = item.get("id", "")
            if not model_id:
                continue
            models.append(catalog.get(model_id) or self._default_model_info(model_id))
        return models

    def _default_model_info(self, model_id: str) -> ModelInfo:
        return ModelInfo(name=model_id, provider=self.name)

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        payload = {"model": model or self.embedding_model, "input": texts}
        response = await self._post("/embeddings", payload)
        data = sorted(response.json().get("data", []), key=lambda d: d.get("index", 0))
        return [item["embedding"] for item in data]

    async def health_check(self) -> bool:
        if self.requires_api_key and not self._has_key:
            return False
        return await super().health_check()

    async def aclose(self) -> None:
        await self._client.aclose()
