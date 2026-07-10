"""Provider registry: builds, caches and health-checks LLM providers.

New providers register themselves via :func:`register_provider` — the core
never needs to change to support another backend (open/closed principle).
Plugins can call ``register_provider`` at load time.
"""

from __future__ import annotations

import asyncio

from jarvis.core.config import JarvisConfig
from jarvis.core.errors import ProviderUnavailableError
from jarvis.core.logging import get_logger
from jarvis.llm.base import LLMProvider
from jarvis.llm.providers import (
    AnthropicProvider,
    DeepSeekProvider,
    GeminiProvider,
    LMStudioProvider,
    LocalProvider,
    MistralProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
)

logger = get_logger("llm.registry")

_PROVIDER_TYPES: dict[str, type[LLMProvider]] = {}


def register_provider(name: str, provider_type: type[LLMProvider]) -> None:
    """Register a provider class under a config name (used by plugins too)."""
    _PROVIDER_TYPES[name] = provider_type


for _cls in (
    AnthropicProvider,
    OpenAIProvider,
    GeminiProvider,
    OllamaProvider,
    LMStudioProvider,
    OpenRouterProvider,
    DeepSeekProvider,
    MistralProvider,
    LocalProvider,
):
    register_provider(_cls.name, _cls)


class ProviderRegistry:
    """Instantiates configured providers lazily and caches health status."""

    def __init__(self, config: JarvisConfig) -> None:
        self._config = config
        self._instances: dict[str, LLMProvider] = {}
        self._health: dict[str, bool] = {}
        self._lock = asyncio.Lock()

    @property
    def available_names(self) -> list[str]:
        """All registered provider names that are not disabled in config."""
        names = set(_PROVIDER_TYPES) | set(self._config.llm.providers)
        return sorted(
            name
            for name in names
            if self._config.llm.providers.get(name) is None
            or self._config.llm.providers[name].enabled
        )

    def get(self, name: str) -> LLMProvider:
        """Return (and cache) the provider instance for *name*."""
        if name in self._instances:
            return self._instances[name]
        provider_type = _PROVIDER_TYPES.get(name)
        if provider_type is None:
            raise ProviderUnavailableError(f"Unknown provider '{name}'", provider=name)
        instance = provider_type(self._config.provider(name))
        self._instances[name] = instance
        return instance

    async def healthy(self, name: str, *, refresh: bool = False) -> bool:
        """Cached health probe for a provider."""
        if not refresh and name in self._health:
            return self._health[name]
        async with self._lock:
            if not refresh and name in self._health:
                return self._health[name]
            try:
                result = await asyncio.wait_for(self.get(name).health_check(), timeout=10.0)
            except Exception:
                result = False
            self._health[name] = result
            return result

    async def healthy_providers(self) -> list[str]:
        """Names of all currently reachable providers (probed concurrently)."""
        names = self.available_names
        results = await asyncio.gather(*(self.healthy(name) for name in names))
        return [name for name, ok in zip(names, results) if ok]

    async def aclose(self) -> None:
        await asyncio.gather(
            *(provider.aclose() for provider in self._instances.values()),
            return_exceptions=True,
        )
        self._instances.clear()
