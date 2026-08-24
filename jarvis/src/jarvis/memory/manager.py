"""MemoryManager: single façade over short-term, long-term and vector memory.

Responsibilities:

* keep the rolling conversation window,
* archive evicted turns into SQLite and the vector store,
* recall relevant facts/episodes for the current query,
* maintain the user profile (name, interests, projects, preferences).
"""

from __future__ import annotations

import uuid
from typing import Any

from jarvis.core.config import JarvisConfig
from jarvis.core.logging import get_logger
from jarvis.llm.base import Message, Role
from jarvis.memory.long_term import Fact, LongTermMemory
from jarvis.memory.rag import RagPipeline
from jarvis.memory.short_term import ShortTermMemory
from jarvis.memory.vector_store import VectorStore

logger = get_logger("memory.manager")


class MemoryManager:
    """Coordinates all memory layers for one assistant instance."""

    def __init__(
        self,
        config: JarvisConfig,
        long_term: LongTermMemory,
        vector_store: VectorStore,
        rag: RagPipeline,
    ) -> None:
        self._config = config
        self.long_term = long_term
        self.vector_store = vector_store
        self.rag = rag
        self.short_term = ShortTermMemory(
            max_messages=config.memory.short_term_max_messages,
            max_chars=config.memory.short_term_max_chars,
        )
        self.session_id = uuid.uuid4().hex

    # -- conversation flow -------------------------------------------------------

    async def add_turn(self, message: Message) -> None:
        """Record a conversation turn and archive anything that falls out of the window."""
        self.short_term.add(message)
        if message.role in (Role.USER, Role.ASSISTANT) and message.content:
            await self.long_term.add_turns(
                self.session_id, [(message.role.value, message.content)]
            )
        evicted = self.short_term.drain_evicted()
        episodic = [
            m for m in evicted if m.role in (Role.USER, Role.ASSISTANT) and len(m.content) > 40
        ]
        if episodic:
            await self.vector_store.add(
                [m.content for m in episodic],
                [
                    {"kind": "episode", "role": m.role.value, "session": self.session_id}
                    for m in episodic
                ],
            )

    def window(self) -> list[Message]:
        return self.short_term.messages()

    def new_session(self) -> str:
        self.short_term.clear()
        self.session_id = uuid.uuid4().hex
        return self.session_id

    # -- recall --------------------------------------------------------------------

    async def recall(self, query: str, *, limit: int = 5) -> str:
        """Build a memory context block for the system prompt."""
        parts: list[str] = []

        facts: list[Fact] = await self.long_term.search_facts(query, limit=limit)
        if facts:
            parts.append(
                "Known facts about the user and their world:\n"
                + "\n".join(f"- ({f.category}) {f.content}" for f in facts)
            )

        episodes = await self.vector_store.query(query, top_k=limit, where={"kind": "episode"})
        strong = [e for e in episodes if e.score > 0.25]
        if strong:
            parts.append(
                "Possibly relevant earlier conversation snippets:\n"
                + "\n".join(f"- {e.text[:300]}" for e in strong)
            )

        profile = await self.long_term.full_profile()
        if profile:
            rendered = ", ".join(f"{k}={v}" for k, v in sorted(profile.items()))
            parts.append(f"User profile: {rendered}")

        return "\n\n".join(parts)

    # -- explicit memory operations --------------------------------------------------

    async def remember(self, content: str, *, category: str = "general", source: str = "") -> int:
        fact_id = await self.long_term.remember_fact(content, category=category, source=source)
        await self.vector_store.add(
            [content], [{"kind": "fact", "category": category, "fact_id": fact_id}]
        )
        return fact_id

    async def update_profile(self, key: str, value: Any) -> None:
        await self.long_term.set_profile(key, value)

    async def stats(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "short_term_messages": len(self.short_term),
            "vector_records": await self.vector_store.count(),
            "facts": len(await self.long_term.all_facts(limit=10_000)),
        }
