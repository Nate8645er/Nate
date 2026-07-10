"""Async event bus used for loose coupling between subsystems.

Voice, GUI, agents and plugins communicate through topic-based events instead
of importing each other. Topics are dotted strings and subscriptions support
trailing wildcards (``"voice.*"``).
"""

from __future__ import annotations

import asyncio
import fnmatch
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from jarvis.core.logging import get_logger

logger = get_logger("core.events")

EventHandler = Callable[["Event"], Awaitable[None] | None]


@dataclass(slots=True)
class Event:
    """A single event on the bus."""

    topic: str
    data: dict[str, Any] = field(default_factory=dict)


class Subscription:
    """Handle returned by :meth:`EventBus.subscribe`; call :meth:`cancel` to detach."""

    def __init__(self, bus: EventBus, pattern: str, handler: EventHandler) -> None:
        self._bus = bus
        self.pattern = pattern
        self.handler = handler

    def cancel(self) -> None:
        self._bus._unsubscribe(self)


class EventBus:
    """Topic-based publish/subscribe with sync and async handlers."""

    def __init__(self) -> None:
        self._subs: list[Subscription] = []

    def subscribe(self, pattern: str, handler: EventHandler) -> Subscription:
        """Subscribe a handler to a topic pattern (supports ``*`` wildcards)."""
        sub = Subscription(self, pattern, handler)
        self._subs.append(sub)
        return sub

    def _unsubscribe(self, sub: Subscription) -> None:
        try:
            self._subs.remove(sub)
        except ValueError:
            pass

    async def publish(self, topic: str, data: dict[str, Any] | None = None) -> None:
        """Publish an event; handler errors are logged, never propagated."""
        event = Event(topic=topic, data=data or {})
        for sub in list(self._subs):
            if not fnmatch.fnmatch(topic, sub.pattern):
                continue
            try:
                outcome = sub.handler(event)
                if inspect.isawaitable(outcome):
                    await outcome
            except Exception:
                logger.exception("Event handler failed for topic %s", topic)

    def publish_nowait(self, topic: str, data: dict[str, Any] | None = None) -> None:
        """Fire-and-forget publish from sync code running inside an event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.publish(topic, data))
            return
        loop.create_task(self.publish(topic, data))
