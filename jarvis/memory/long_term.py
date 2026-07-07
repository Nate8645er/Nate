"""Long-term memory: durable facts, conversations, and project knowledge.

Backed by SQLite in the JARVIS data directory by default; the same schema
works against PostgreSQL in Docker (see JARVIS_DATABASE_URL). Kept
deliberately dependency-free — stdlib sqlite3 with a thin async facade.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL DEFAULT 'fact',      -- fact | preference | project | knowledge
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_facts_kind_subject ON facts(kind, subject);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session);
"""


class LongTermMemory:
    def __init__(self, path: Path | str = ":memory:") -> None:
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = asyncio.Lock()
        self._closed = False
        self._db.executescript(_SCHEMA)
        self._db.commit()

    async def _execute(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        # Queries at personal scale are sub-millisecond; running them inline
        # under the lock keeps the connection single-threaded (sqlite3 is not
        # thread-safe) without an executor round-trip.
        async with self._lock:
            if self._closed:
                return []
            cur = self._db.execute(sql, params)
            rows = cur.fetchall()
            cur.close()
            self._db.commit()
            return rows

    # --- facts / knowledge base ---

    async def remember(self, subject: str, content: str, kind: str = "fact") -> int:
        rows = await self._execute(
            "INSERT INTO facts (kind, subject, content, created_at) VALUES (?, ?, ?, ?) RETURNING id",
            (kind, subject, content, time.time()),
        )
        return int(rows[0]["id"])

    async def recall(
        self, query: str = "", kind: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM facts WHERE 1=1"
        params: list[Any] = []
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        if query:
            sql += " AND (subject LIKE ? OR content LIKE ?)"
            like = f"%{query}%"
            params += [like, like]
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = await self._execute(sql, tuple(params))
        return [dict(r) for r in rows]

    async def forget(self, fact_id: int) -> None:
        await self._execute("DELETE FROM facts WHERE id = ?", (fact_id,))

    # --- conversation history ---

    async def log_message(
        self, session: str, role: str, content: str, meta: dict[str, Any] | None = None
    ) -> None:
        await self._execute(
            "INSERT INTO conversations (session, role, content, meta, created_at) VALUES (?, ?, ?, ?, ?)",
            (session, role, content, json.dumps(meta or {}), time.time()),
        )

    async def conversation(self, session: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = await self._execute(
            "SELECT role, content, meta, created_at FROM conversations "
            "WHERE session = ? ORDER BY id DESC LIMIT ?",
            (session, limit),
        )
        result = [dict(r) for r in reversed(rows)]
        for r in result:
            r["meta"] = json.loads(r["meta"])
        return result

    def close(self) -> None:
        self._closed = True
        self._db.close()
