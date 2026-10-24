"""LLM provider abstraction.

One interface, several backends:
  * anthropic — Claude via the Anthropic API
  * openai    — any OpenAI-compatible endpoint (incl. LM Studio, vLLM, Groq)
  * ollama    — local models via the Ollama HTTP API
  * echo      — offline fallback so the whole OS keeps working without keys

"auto" picks the first configured backend in the order above.
All HTTP is done with httpx directly, so no provider SDK is required.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from jarvis.config import Settings

log = logging.getLogger(__name__)


@dataclass(slots=True)
class ChatMessage:
    role: str  # system | user | assistant | tool
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ChatResult:
    text: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""


class LLMProvider(Protocol):
    name: str

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str = "",
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> ChatResult: ...


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str = "",
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> ChatResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = tools
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        text_parts, tool_calls = [], []
        for block in data.get("content", []):
            if block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append(
                    {"id": block["id"], "name": block["name"], "arguments": block["input"]}
                )
        return ChatResult(text="".join(text_parts), tool_calls=tool_calls, model=self.model)


class OpenAICompatProvider:
    name = "openai"

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str = "",
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> ChatResult:
        msgs: list[dict[str, Any]] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs += [{"role": m.role, "content": m.content} for m in messages]
        payload: dict[str, Any] = {"model": self.model, "messages": msgs, "max_tokens": max_tokens}
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("input_schema", {}),
                    },
                }
                for t in tools
            ]
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )
            resp.raise_for_status()
            data = resp.json()
        choice = data["choices"][0]["message"]
        tool_calls = [
            {
                "id": tc.get("id", ""),
                "name": tc["function"]["name"],
                "arguments": json.loads(tc["function"].get("arguments") or "{}"),
            }
            for tc in (choice.get("tool_calls") or [])
        ]
        return ChatResult(text=choice.get("content") or "", tool_calls=tool_calls, model=self.model)


class OllamaProvider(OpenAICompatProvider):
    """Ollama exposes an OpenAI-compatible endpoint under /v1."""

    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        super().__init__(api_key="", base_url=f"{base_url.rstrip('/')}/v1", model=model)


class EchoProvider:
    """Offline fallback: no external calls, deterministic, honest about it."""

    name = "echo"

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str = "",
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> ChatResult:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return ChatResult(
            text=(
                "Ich laufe gerade ohne angebundenes Sprachmodell (Echo-Modus). "
                f"Deine Nachricht war: „{last_user}“. "
                "Hinterlege einen API-Key (Anthropic/OpenAI) oder starte Ollama, "
                "dann antworte ich richtig."
            ),
            model="echo",
        )


def create_provider(cfg: Settings) -> LLMProvider:
    choice = cfg.llm_provider
    if choice in ("auto", "anthropic") and cfg.anthropic_api_key:
        return AnthropicProvider(cfg.anthropic_api_key, cfg.anthropic_model)
    if choice in ("auto", "openai") and cfg.openai_api_key:
        return OpenAICompatProvider(cfg.openai_api_key, cfg.openai_base_url, cfg.openai_model)
    if choice == "ollama":
        return OllamaProvider(cfg.ollama_base_url, cfg.ollama_model)
    if choice == "auto":
        # Probe for a local Ollama; use it if it answers.
        try:
            resp = httpx.get(f"{cfg.ollama_base_url}/api/tags", timeout=1.5)
            if resp.status_code == 200:
                return OllamaProvider(cfg.ollama_base_url, cfg.ollama_model)
        except httpx.HTTPError:
            pass
    if choice not in ("auto", "echo"):
        log.warning("LLM provider %r not configured; falling back to echo", choice)
    return EchoProvider()
