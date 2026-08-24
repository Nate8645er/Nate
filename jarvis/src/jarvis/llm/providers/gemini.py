"""Google Gemini provider using the public Generative Language API over httpx."""

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


class GeminiProvider(LLMProvider):
    name = "gemini"
    default_base_url = "https://generativelanguage.googleapis.com/v1beta"
    default_model = "gemini-2.5-flash"
    embedding_model = "text-embedding-004"
    model_catalog = [
        ModelInfo(name="gemini-2.5-pro", provider="gemini", context_window=1_000_000, supports_vision=True, cost_tier=2, quality=9),
        ModelInfo(name="gemini-2.5-flash", provider="gemini", context_window=1_000_000, supports_vision=True, cost_tier=1, quality=7),
        ModelInfo(name="gemini-2.0-flash", provider="gemini", context_window=1_000_000, supports_vision=True, cost_tier=1, quality=6),
    ]

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self.base_url = (config.base_url or self.default_base_url).rstrip("/")
        self._api_key = config.api_key.get_secret_value() if config.api_key else ""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Content-Type": "application/json", **config.extra_headers},
            timeout=config.timeout_seconds,
        )

    # -- mapping -----------------------------------------------------------------

    def _to_wire(self, messages: list[Message]) -> tuple[str, list[dict[str, Any]]]:
        system_parts: list[str] = []
        contents: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role is Role.SYSTEM:
                system_parts.append(msg.content)
                continue
            if msg.role is Role.TOOL:
                contents.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": msg.name or "tool",
                                    "response": {"result": msg.content},
                                }
                            }
                        ],
                    }
                )
                continue
            parts: list[dict[str, Any]] = []
            if msg.content:
                parts.append({"text": msg.content})
            for img in msg.images:
                parts.append(
                    {"inlineData": {"mimeType": img.media_type, "data": img.data_base64}}
                )
            for call in msg.tool_calls:
                parts.append({"functionCall": {"name": call.name, "args": call.arguments}})
            contents.append(
                {
                    "role": "model" if msg.role is Role.ASSISTANT else "user",
                    "parts": parts or [{"text": ""}],
                }
            )
        return "\n\n".join(system_parts), contents

    def _build_payload(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None,
        options: ChatOptions | None,
    ) -> tuple[str, dict[str, Any]]:
        opts = options or ChatOptions()
        model = opts.model or self._config.default_model or self.default_model
        system, contents = self._to_wire(messages)
        generation: dict[str, Any] = {}
        if opts.temperature is not None:
            generation["temperature"] = opts.temperature
        if opts.max_tokens is not None:
            generation["maxOutputTokens"] = opts.max_tokens
        if opts.stop:
            generation["stopSequences"] = opts.stop
        if opts.json_mode:
            generation["responseMimeType"] = "application/json"
        payload: dict[str, Any] = {"contents": contents}
        if generation:
            payload["generationConfig"] = generation
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if tools:
            payload["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "parameters": _strip_unsupported(t.parameters),
                        }
                        for t in tools
                    ]
                }
            ]
        return model, payload

    @staticmethod
    def _parse_candidate(body: dict[str, Any], model: str) -> ChatResponse:
        candidates = body.get("candidates") or []
        if not candidates:
            raise ProviderError("Gemini returned no candidates", provider="gemini")
        candidate = candidates[0]
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for i, part in enumerate(candidate.get("content", {}).get("parts", [])):
            if "text" in part:
                text_parts.append(part["text"])
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    ToolCall(id=f"call_{i}", name=fc.get("name", ""), arguments=fc.get("args") or {})
                )
        meta = body.get("usageMetadata") or {}
        return ChatResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            model=model,
            provider="gemini",
            finish_reason=(candidate.get("finishReason") or "stop").lower(),
            usage=Usage(
                input_tokens=meta.get("promptTokenCount", 0),
                output_tokens=meta.get("candidatesTokenCount", 0),
            ),
        )

    async def _post(self, path: str, payload: dict[str, Any]) -> httpx.Response:
        try:
            response = await self._client.post(path, json=payload, params={"key": self._api_key})
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError("Cannot reach Gemini API", provider=self.name, cause=exc) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc), provider=self.name, cause=exc) from exc
        if response.status_code >= 400:
            raise ProviderError(
                f"Gemini returned HTTP {response.status_code}: {response.text[:500]}",
                provider=self.name,
                status_code=response.status_code,
            )
        return response

    # -- LLMProvider ----------------------------------------------------------------

    async def chat(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
    ) -> ChatResponse:
        model, payload = self._build_payload(messages, tools, options)
        response = await self._post(f"/models/{model}:generateContent", payload)
        return self._parse_candidate(response.json(), model)

    async def chat_stream(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
    ) -> AsyncIterator[StreamChunk]:
        model, payload = self._build_payload(messages, tools, options)
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        finish_reason = "stop"
        usage = Usage()
        try:
            async with self._client.stream(
                "POST",
                f"/models/{model}:streamGenerateContent",
                json=payload,
                params={"key": self._api_key, "alt": "sse"},
            ) as resp:
                if resp.status_code >= 400:
                    text = (await resp.aread()).decode("utf-8", "replace")
                    raise ProviderError(
                        f"Gemini returned HTTP {resp.status_code}: {text[:500]}",
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
                    for candidate in event.get("candidates") or []:
                        if candidate.get("finishReason"):
                            finish_reason = candidate["finishReason"].lower()
                        for part in candidate.get("content", {}).get("parts", []):
                            if "text" in part:
                                text_parts.append(part["text"])
                                yield StreamChunk(delta=part["text"])
                            elif "functionCall" in part:
                                fc = part["functionCall"]
                                tool_calls.append(
                                    ToolCall(
                                        id=f"call_{len(tool_calls)}",
                                        name=fc.get("name", ""),
                                        arguments=fc.get("args") or {},
                                    )
                                )
                    meta = event.get("usageMetadata") or {}
                    if meta:
                        usage = Usage(
                            input_tokens=meta.get("promptTokenCount", 0),
                            output_tokens=meta.get("candidatesTokenCount", 0),
                        )
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError("Cannot reach Gemini API", provider=self.name, cause=exc) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(str(exc), provider=self.name, cause=exc) from exc

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
        if not self._api_key:
            raise ProviderUnavailableError("Gemini API key not configured", provider=self.name)
        try:
            response = await self._client.get("/models", params={"key": self._api_key})
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError("Cannot reach Gemini API", provider=self.name, cause=exc) from exc
        if response.status_code >= 400:
            raise ProviderUnavailableError(
                f"Gemini /models returned HTTP {response.status_code}", provider=self.name
            )
        catalog = {info.name: info for info in self.model_catalog}
        models: list[ModelInfo] = []
        for item in response.json().get("models", []):
            model_id = str(item.get("name", "")).removeprefix("models/")
            if "generateContent" not in (item.get("supportedGenerationMethods") or []):
                continue
            models.append(
                catalog.get(model_id)
                or ModelInfo(
                    name=model_id,
                    provider=self.name,
                    context_window=item.get("inputTokenLimit", 128_000),
                    supports_vision=True,
                    cost_tier=1,
                    quality=6,
                )
            )
        return models

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        model_id = model or self.embedding_model
        payload = {
            "requests": [
                {"model": f"models/{model_id}", "content": {"parts": [{"text": text}]}}
                for text in texts
            ]
        }
        response = await self._post(f"/models/{model_id}:batchEmbedContents", payload)
        return [item.get("values", []) for item in response.json().get("embeddings", [])]

    async def health_check(self) -> bool:
        return bool(self._api_key) and await super().health_check()

    async def aclose(self) -> None:
        await self._client.aclose()


def _strip_unsupported(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove JSON-Schema keywords Gemini's function declarations reject."""
    banned = {"additionalProperties", "$schema", "default", "examples"}
    cleaned: dict[str, Any] = {}
    for key, value in schema.items():
        if key in banned:
            continue
        if isinstance(value, dict):
            cleaned[key] = _strip_unsupported(value)
        elif isinstance(value, list):
            cleaned[key] = [
                _strip_unsupported(v) if isinstance(v, dict) else v for v in value
            ]
        else:
            cleaned[key] = value
    return cleaned
