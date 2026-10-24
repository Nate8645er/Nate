"""Unified memory facade: short-term + long-term + vector recall.

Agents talk to this one object; the manager decides where things live and
assembles "context packs" (recent window + semantically relevant long-term
memories) for LLM prompts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.memory.long_term import LongTermMemory
from jarvis.memory.short_term import ShortTermMemory
from jarvis.memory.vector import VectorStore, create_vector_store


class MemoryManager:
    def __init__(
        self,
        data_dir: Path,
        vector_backend: str = "auto",
        window: int = 50,
        db_path: Path | str | None = None,
    ) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self.short_term = ShortTermMemory(window=window)
        self.long_term = LongTermMemory(db_path or data_dir / "jarvis.db")
        self.vector: VectorStore = create_vector_store(vector_backend, str(data_dir / "vectors"))

    # --- conversational flow ---

    async def observe(self, session: str, role: str, content: str, **meta: Any) -> None:
        """Record a message everywhere it belongs."""
        self.short_term.add(session, role, content, **meta)
        await self.long_term.log_message(session, role, content, meta)
        if role == "user" and len(content) > 12:
            await self.vector.add(content, {"session": session, "role": role})

    async def context_pack(self, session: str, query: str, limit: int = 8) -> dict[str, Any]:
        """Everything an agent needs to answer in context."""
        recent = [m.to_dict() for m in self.short_term.recall(session, limit=limit)]
        related = await self.vector.search(query, limit=4) if query else []
        facts = await self.long_term.recall(kind="fact", limit=10)
        preferences = await self.long_term.recall(kind="preference", limit=10)
        return {
            "recent": recent,
            "related": related,
            "facts": facts,
            "preferences": preferences,
        }

    # --- explicit knowledge ---

    async def remember(self, subject: str, content: str, kind: str = "fact") -> int:
        fact_id = await self.long_term.remember(subject, content, kind)
        await self.vector.add(f"{subject}: {content}", {"kind": kind, "fact_id": fact_id})
        return fact_id

    async def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        return await self.vector.search(query, limit=limit)

    def close(self) -> None:
        self.long_term.close()
