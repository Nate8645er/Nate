"""Async event bus — the nervous system of JARVIS.

Every subsystem (agents, skills, voice, UI) communicates through events so
components stay decoupled and horizontally scalable. Topics are dotted
strings ("agent.task.completed"); subscriptions support trailing wildcards
("agent.*", "*").
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

log = logging.getLogger(__name__)

Handler = Callable[["Event"], Awaitable[None]]


@dataclass(slots=True)
class Event:
    topic: str
    data: dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp,
        }


class EventBus:
    """In-process async pub/sub with wildcard topics and bounded history."""

    def __init__(self, history_size: int = 500) -> None:
        self._subs: list[tuple[str, Handler]] = []
        self.history: deque[Event] = deque(maxlen=history_size)

    def subscribe(self, pattern: str, handler: Handler) -> Callable[[], None]:
        """Subscribe to a topic pattern. Returns an unsubscribe callable."""
        entry = (pattern, handler)
        self._subs.append(entry)

        def unsubscribe() -> None:
            if entry in self._subs:
                self._subs.remove(entry)

        return unsubscribe

    async def publish(
        self, topic: str, data: dict[str, Any] | None = None, source: str = "system"
    ) -> Event:
        event = Event(topic=topic, data=data or {}, source=source)
        self.history.append(event)
        handlers = [h for pattern, h in list(self._subs) if fnmatch.fnmatch(topic, pattern)]
        results = await asyncio.gather(*(h(event) for h in handlers), return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                log.exception("Event handler failed for %s", topic, exc_info=result)
        return event

    async def wait_for(self, pattern: str, timeout: float | None = None) -> Event:
        """Wait for the next event matching *pattern*."""
        future: asyncio.Future[Event] = asyncio.get_running_loop().create_future()

        async def handler(event: Event) -> None:
            if not future.done():
                future.set_result(event)

        unsubscribe = self.subscribe(pattern, handler)
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            unsubscribe()
