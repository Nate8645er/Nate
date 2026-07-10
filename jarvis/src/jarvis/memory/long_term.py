"""Long-term memory backed by SQLite (aiosqlite) with full-text search.

Stores conversation history, extracted facts, the user profile, interests and
projects. Facts are searchable via FTS5 so relevant knowledge can be recalled
into future prompts.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

from jarvis.core.errors import MemoryStoreError
from jarvis.core.logging import get_logger

logger = get_logger("memory.long_term")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);

CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL DEFAULT 'general',
    content TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
    content, category, content='facts', content_rowid='id'
);
CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
    INSERT INTO facts_fts(rowid, content, category) VALUES (new.id, new.content, new.category);
END;
CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, content, category)
    VALUES ('delete', old.id, old.content, old.category);
END;
CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, content, category)
    VALUES ('delete', old.id, old.content, old.category);
    INSERT INTO facts_fts(rowid, content, category) VALUES (new.id, new.content, new.category);
END;

CREATE TABLE IF NOT EXISTS profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    due_at TEXT,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class Fact:
    id: int
    category: str
    content: str
    source: str
    created_at: str


@dataclass(slots=True)
class TaskItem:
    id: int
    title: str
    details: str
    due_at: str | None
    done: bool


class LongTermMemory:
    """Async SQLite persistence layer."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def open(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise MemoryStoreError("Long-term memory is not opened; call open() first")
        return self._db

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    # -- conversations ---------------------------------------------------------

    async def add_turns(self, session_id: str, turns: list[tuple[str, str]]) -> None:
        """Persist (role, content) turns for a session."""
        if not turns:
            return
        await self.db.executemany(
            "INSERT INTO conversations(session_id, role, content, created_at) VALUES (?,?,?,?)",
            [(session_id, role, content, _now()) for role, content in turns],
        )
        await self.db.commit()

    async def recent_turns(self, session_id: str, limit: int = 50) -> list[tuple[str, str]]:
        cursor = await self.db.execute(
            "SELECT role, content FROM conversations WHERE session_id=? "
            "ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        return [(row["role"], row["content"]) for row in reversed(rows)]

    async def sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        cursor = await self.db.execute(
            "SELECT session_id, COUNT(*) AS turns, MAX(created_at) AS last_at "
            "FROM conversations GROUP BY session_id ORDER BY last_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    # -- facts -----------------------------------------------------------------

    async def remember_fact(
        self, content: str, *, category: str = "general", source: str = ""
    ) -> int:
        now = _now()
        cursor = await self.db.execute(
            "INSERT INTO facts(category, content, source, created_at, updated_at) "
            "VALUES (?,?,?,?,?)",
            (category, content, source, now, now),
        )
        await self.db.commit()
        return int(cursor.lastrowid or 0)

    async def forget_fact(self, fact_id: int) -> bool:
        cursor = await self.db.execute("DELETE FROM facts WHERE id=?", (fact_id,))
        await self.db.commit()
        return cursor.rowcount > 0

    async def search_facts(self, query: str, limit: int = 10) -> list[Fact]:
        """FTS5 prefix search; falls back to LIKE for queries FTS cannot parse."""
        tokens = [t for t in re.findall(r"\w+", query) if len(t) > 1]
        match = " OR ".join(f'"{t}"*' for t in tokens) or query
        try:
            cursor = await self.db.execute(
                "SELECT f.id, f.category, f.content, f.source, f.created_at "
                "FROM facts_fts JOIN facts f ON f.id = facts_fts.rowid "
                "WHERE facts_fts MATCH ? ORDER BY rank LIMIT ?",
                (match, limit),
            )
        except aiosqlite.OperationalError:
            cursor = await self.db.execute(
                "SELECT id, category, content, source, created_at FROM facts "
                "WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{query}%", limit),
            )
        return [Fact(**dict(row)) for row in await cursor.fetchall()]

    async def all_facts(self, category: str | None = None, limit: int = 100) -> list[Fact]:
        if category:
            cursor = await self.db.execute(
                "SELECT id, category, content, source, created_at FROM facts "
                "WHERE category=? ORDER BY id DESC LIMIT ?",
                (category, limit),
            )
        else:
            cursor = await self.db.execute(
                "SELECT id, category, content, source, created_at FROM facts "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        return [Fact(**dict(row)) for row in await cursor.fetchall()]

    # -- profile ------------------------------------------------------------------

    async def set_profile(self, key: str, value: Any) -> None:
        await self.db.execute(
            "INSERT INTO profile(key, value, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, json.dumps(value, ensure_ascii=False), _now()),
        )
        await self.db.commit()

    async def get_profile(self, key: str, default: Any = None) -> Any:
        cursor = await self.db.execute("SELECT value FROM profile WHERE key=?", (key,))
        row = await cursor.fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    async def full_profile(self) -> dict[str, Any]:
        cursor = await self.db.execute("SELECT key, value FROM profile")
        return {row["key"]: json.loads(row["value"]) for row in await cursor.fetchall()}

    # -- tasks / reminders -----------------------------------------------------------

    async def add_task(self, title: str, details: str = "", due_at: str | None = None) -> int:
        cursor = await self.db.execute(
            "INSERT INTO tasks(title, details, due_at, created_at) VALUES (?,?,?,?)",
            (title, details, due_at, _now()),
        )
        await self.db.commit()
        return int(cursor.lastrowid or 0)

    async def complete_task(self, task_id: int) -> bool:
        cursor = await self.db.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
        await self.db.commit()
        return cursor.rowcount > 0

    async def list_tasks(self, include_done: bool = False) -> list[TaskItem]:
        query = "SELECT id, title, details, due_at, done FROM tasks"
        if not include_done:
            query += " WHERE done=0"
        query += " ORDER BY COALESCE(due_at, created_at)"
        cursor = await self.db.execute(query)
        return [
            TaskItem(
                id=row["id"],
                title=row["title"],
                details=row["details"],
                due_at=row["due_at"],
                done=bool(row["done"]),
            )
            for row in await cursor.fetchall()
        ]
