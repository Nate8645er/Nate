"""Automatic model selection.

The router scores every model offered by every healthy provider against the
task requirements (vision, tools, context size, cost ceiling, local
preference) and picks the best one. Explicit ``provider``/``model`` settings
in the config always win.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from jarvis.core.config import JarvisConfig
from jarvis.core.errors import ProviderUnavailableError
from jarvis.core.logging import get_logger
from jarvis.llm.base import (
    ChatOptions,
    ChatResponse,
    LLMProvider,
    Message,
    ModelInfo,
    StreamChunk,
    ToolSpec,
)
from jarvis.llm.registry import ProviderRegistry

logger = get_logger("llm.router")


@dataclass(slots=True)
class TaskRequirements:
    """What the caller needs from a model."""

    needs_vision: bool = False
    needs_tools: bool = False
    min_context: int = 8_000
    max_cost_tier: int | None = None  # None => config value
    prefer_local: bool | None = None  # None => config value
    min_quality: int = 0


@dataclass(slots=True)
class RoutedModel:
    provider: LLMProvider
    model: ModelInfo
    score: float = field(default=0.0)


class ModelRouter:
    """Chooses provider+model per request and exposes a uniform chat API."""

    def __init__(self, config: JarvisConfig, registry: ProviderRegistry) -> None:
        self._config = config
        self._registry = registry
        self._model_cache: dict[str, list[ModelInfo]] = {}

    async def _models_for(self, provider_name: str) -> list[ModelInfo]:
        if provider_name not in self._model_cache:
            try:
                self._model_cache[provider_name] = await self._registry.get(
                    provider_name
                ).list_models()
            except Exception as exc:
                logger.debug("Could not list models for %s: %s", provider_name, exc)
                self._model_cache[provider_name] = []
        return self._model_cache[provider_name]

    def invalidate_cache(self) -> None:
        self._model_cache.clear()

    def _score(self, model: ModelInfo, req: TaskRequirements) -> float | None:
        """Score a model for the task; ``None`` means unusable."""
        if req.needs_vision and not model.supports_vision:
            return None
        if req.needs_tools and not model.supports_tools:
            return None
        if model.context_window < req.min_context:
            return None
        if model.quality < req.min_quality:
            return None
        max_cost = req.max_cost_tier if req.max_cost_tier is not None else self._config.llm.max_cost_tier
        if model.cost_tier > max_cost:
            return None
        prefer_local = (
            req.prefer_local if req.prefer_local is not None else self._config.llm.prefer_local
        )
        score = float(model.quality) * 10.0
        score -= model.cost_tier * 2.0  # cheaper wins ties
        if prefer_local:
            score += 50.0 if model.local else 0.0
        return score

    async def select(self, requirements: TaskRequirements | None = None) -> RoutedModel:
        """Pick the best available provider+model for the requirements."""
        req = requirements or TaskRequirements()

        # Explicit configuration wins.
        if self._config.llm.default_provider:
            name = self._config.llm.default_provider
            if not await self._registry.healthy(name):
                raise ProviderUnavailableError(
                    f"Configured provider '{name}' is not available", provider=name
                )
            provider = self._registry.get(name)
            models = await self._models_for(name)
            wanted = self._config.llm.default_model
            model = next((m for m in models if m.name == wanted), None) if wanted else None
            if model is None:
                model = ModelInfo(
                    name=wanted or str(getattr(provider, "default_model", "default")),
                    provider=name,
                )
            return RoutedModel(provider=provider, model=model)

        best: RoutedModel | None = None
        for name in await self._registry.healthy_providers():
            provider = self._registry.get(name)
            for model in await self._models_for(name):
                score = self._score(model, req)
                if score is None:
                    continue
                if best is None or score > best.score:
                    best = RoutedModel(provider=provider, model=model, score=score)
        if best is None:
            raise ProviderUnavailableError(
                "No available model satisfies the requirements. "
                "Configure at least one provider (API key or local server)."
            )
        logger.info("Routed to %s/%s (score %.1f)", best.model.provider, best.model.name, best.score)
        return best

    def _options(self, routed: RoutedModel, options: ChatOptions | None) -> ChatOptions:
        opts = options or ChatOptions()
        return opts.model_copy(
            update={
                "model": opts.model or routed.model.name,
                "temperature": (
                    opts.temperature
                    if opts.temperature is not None
                    else self._config.llm.temperature
                ),
                "max_tokens": opts.max_tokens or self._config.llm.max_tokens,
            }
        )

    async def chat(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
        requirements: TaskRequirements | None = None,
    ) -> ChatResponse:
        req = requirements or TaskRequirements(
            needs_tools=bool(tools),
            needs_vision=any(m.images for m in messages),
        )
        routed = await self.select(req)
        return await routed.provider.chat(
            messages, tools=tools, options=self._options(routed, options)
        )

    async def chat_stream(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        options: ChatOptions | None = None,
        requirements: TaskRequirements | None = None,
    ) -> AsyncIterator[StreamChunk]:
        req = requirements or TaskRequirements(
            needs_tools=bool(tools),
            needs_vision=any(m.images for m in messages),
        )
        routed = await self.select(req)
        async for chunk in routed.provider.chat_stream(
            messages, tools=tools, options=self._options(routed, options)
        ):
            yield chunk

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed via the configured embedding provider (used by the vector store)."""
        name = self._config.memory.embedding_provider
        if not name:
            raise ProviderUnavailableError("No embedding provider configured")
        provider = self._registry.get(name)
        return await provider.embed(texts, model=self._config.memory.embedding_model)
