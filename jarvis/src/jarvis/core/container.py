"""A small, explicit dependency-injection container.

No global state, no import-time magic: services are registered by type (and an
optional name) as either singletons, instances or factories, and resolved
lazily. Async factories are supported via :meth:`ServiceContainer.aresolve`.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from jarvis.core.errors import ConfigurationError

T = TypeVar("T")

_FactoryT = Callable[["ServiceContainer"], Any]


class ServiceContainer:
    """Registry of application services with lifetime management."""

    def __init__(self) -> None:
        self._factories: dict[tuple[type, str], _FactoryT] = {}
        self._singleton_keys: set[tuple[type, str]] = set()
        self._instances: dict[tuple[type, str], Any] = {}
        self._lock = asyncio.Lock()
        self._closers: list[Callable[[], Awaitable[None] | None]] = []

    # -- registration ------------------------------------------------------

    def register_instance(self, interface: type[T], instance: T, *, name: str = "") -> None:
        """Register an already-constructed object as a singleton."""
        self._instances[(interface, name)] = instance

    def register_singleton(
        self, interface: type[T], factory: Callable[[ServiceContainer], T], *, name: str = ""
    ) -> None:
        """Register a factory whose result is created once and cached."""
        key = (interface, name)
        self._factories[key] = factory
        self._singleton_keys.add(key)

    def register_factory(
        self, interface: type[T], factory: Callable[[ServiceContainer], T], *, name: str = ""
    ) -> None:
        """Register a factory invoked on every resolution (transient lifetime)."""
        key = (interface, name)
        self._factories[key] = factory
        self._singleton_keys.discard(key)

    def on_close(self, closer: Callable[[], Awaitable[None] | None]) -> None:
        """Register a shutdown hook, run in reverse order by :meth:`aclose`."""
        self._closers.append(closer)

    # -- resolution --------------------------------------------------------

    def has(self, interface: type, *, name: str = "") -> bool:
        key = (interface, name)
        return key in self._instances or key in self._factories

    def resolve(self, interface: type[T], *, name: str = "") -> T:
        """Resolve a service synchronously. Raises if the factory is async."""
        key = (interface, name)
        if key in self._instances:
            return self._instances[key]
        factory = self._factories.get(key)
        if factory is None:
            raise ConfigurationError(
                f"No service registered for {interface.__name__!r}"
                + (f" (name={name!r})" if name else "")
            )
        result = factory(self)
        if inspect.isawaitable(result):
            raise ConfigurationError(
                f"Service {interface.__name__!r} has an async factory; use aresolve()"
            )
        if key in self._singleton_keys:
            self._instances[key] = result
        return result

    async def aresolve(self, interface: type[T], *, name: str = "") -> T:
        """Resolve a service, awaiting async factories and caching singletons safely."""
        key = (interface, name)
        if key in self._instances:
            return self._instances[key]
        async with self._lock:
            if key in self._instances:
                return self._instances[key]
            factory = self._factories.get(key)
            if factory is None:
                raise ConfigurationError(
                    f"No service registered for {interface.__name__!r}"
                    + (f" (name={name!r})" if name else "")
                )
            result = factory(self)
            if inspect.isawaitable(result):
                result = await result
            if key in self._singleton_keys:
                self._instances[key] = result
            return result

    async def aclose(self) -> None:
        """Run shutdown hooks (latest registered first)."""
        for closer in reversed(self._closers):
            outcome = closer()
            if inspect.isawaitable(outcome):
                await outcome
        self._closers.clear()
