"""Short-term (working) memory: a bounded rolling window per context."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MemoryItem:
    role: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "meta": self.meta,
            "timestamp": self.timestamp,
        }


class ShortTermMemory:
    def __init__(self, window: int = 50) -> None:
        self._contexts: dict[str, deque[MemoryItem]] = defaultdict(lambda: deque(maxlen=window))

    def add(self, context: str, role: str, content: str, **meta: Any) -> MemoryItem:
        item = MemoryItem(role=role, content=content, meta=meta)
        self._contexts[context].append(item)
        return item

    def recall(self, context: str, limit: int | None = None) -> list[MemoryItem]:
        items = list(self._contexts[context])
        return items[-limit:] if limit else items

    def clear(self, context: str) -> None:
        self._contexts.pop(context, None)
