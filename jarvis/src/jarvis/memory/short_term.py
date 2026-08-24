"""Short-term (working) memory: the rolling conversation window.

Keeps recent turns within message- and character-budgets so prompts stay
inside the model context. Older turns are handed to the long-term store by
the :class:`~jarvis.memory.manager.MemoryManager`.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from jarvis.llm.base import Message, Role


class ShortTermMemory:
    """Bounded conversation buffer with overflow reporting."""

    def __init__(self, max_messages: int = 60, max_chars: int = 60_000) -> None:
        self.max_messages = max_messages
        self.max_chars = max_chars
        self._messages: deque[Message] = deque()
        self._evicted: list[Message] = []

    def add(self, message: Message) -> None:
        self._messages.append(message)
        self._enforce_limits()

    def extend(self, messages: Iterable[Message]) -> None:
        for message in messages:
            self.add(message)

    def _enforce_limits(self) -> None:
        while len(self._messages) > self.max_messages:
            self._evicted.append(self._messages.popleft())
        while self._total_chars() > self.max_chars and len(self._messages) > 2:
            self._evicted.append(self._messages.popleft())

    def _total_chars(self) -> int:
        return sum(len(m.content) for m in self._messages)

    def messages(self) -> list[Message]:
        """Current window, oldest first, with dangling tool results trimmed."""
        window = list(self._messages)
        # A window must not start with an orphaned tool result.
        while window and window[0].role is Role.TOOL:
            window.pop(0)
        return window

    def drain_evicted(self) -> list[Message]:
        """Return and clear turns that fell out of the window (for archival)."""
        evicted, self._evicted = self._evicted, []
        return evicted

    def clear(self) -> None:
        self._messages.clear()
        self._evicted.clear()

    def __len__(self) -> int:
        return len(self._messages)
