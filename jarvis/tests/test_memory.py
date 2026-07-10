"""Tests for the memory subsystem."""

from __future__ import annotations

import pytest

from jarvis.core.config import JarvisConfig
from jarvis.llm.base import Message
from jarvis.memory.long_term import LongTermMemory
from jarvis.memory.manager import MemoryManager
from jarvis.memory.rag import RagPipeline, chunk_text
from jarvis.memory.short_term import ShortTermMemory
from jarvis.memory.vector_store import HashingEmbedder, LocalVectorStore


class TestShortTerm:
    def test_eviction_by_count(self) -> None:
        stm = ShortTermMemory(max_messages=3, max_chars=10_000)
        for i in range(5):
            stm.add(Message.user(f"msg {i}"))
        assert len(stm) == 3
        evicted = stm.drain_evicted()
        assert [m.content for m in evicted] == ["msg 0", "msg 1"]

    def test_eviction_by_chars(self) -> None:
        stm = ShortTermMemory(max_messages=100, max_chars=50)
        for _ in range(5):
            stm.add(Message.user("x" * 20))
        assert sum(len(m.content) for m in stm.messages()) <= 50 or len(stm) == 2


class TestLongTerm:
    @pytest.fixture()
    async def store(self, config: JarvisConfig):
        memory = LongTermMemory(config.data_dir / "test.db")
        await memory.open()
        yield memory
        await memory.close()

    async def test_facts_roundtrip(self, store: LongTermMemory) -> None:
        fact_id = await store.remember_fact("The user lives in Zurich", category="profile")
        results = await store.search_facts("Zurich")
        assert any(f.id == fact_id for f in results)
        assert await store.forget_fact(fact_id)
        assert not await store.search_facts("Zurich")

    async def test_prefix_search(self, store: LongTermMemory) -> None:
        await store.remember_fact("User likes cyan HUDs")
        assert await store.search_facts("HUD")

    async def test_profile(self, store: LongTermMemory) -> None:
        await store.set_profile("name", "Nate")
        await store.set_profile("name", "Nate S.")
        assert await store.get_profile("name") == "Nate S."
        assert (await store.full_profile())["name"] == "Nate S."

    async def test_tasks(self, store: LongTermMemory) -> None:
        task_id = await store.add_task("Buy arc reactor parts", due_at="2026-08-01T10:00:00")
        open_tasks = await store.list_tasks()
        assert any(t.id == task_id for t in open_tasks)
        assert await store.complete_task(task_id)
        assert all(t.id != task_id for t in await store.list_tasks())

    async def test_conversations(self, store: LongTermMemory) -> None:
        await store.add_turns("s1", [("user", "hello"), ("assistant", "hi")])
        turns = await store.recent_turns("s1")
        assert turns == [("user", "hello"), ("assistant", "hi")]


class TestVectorStore:
    async def test_add_query_delete(self, tmp_path) -> None:
        store = LocalVectorStore(HashingEmbedder(), tmp_path / "vec.json")
        ids = await store.add(
            ["the arc reactor powers the suit", "the toaster makes bread"],
            [{"kind": "doc"}, {"kind": "doc"}],
        )
        results = await store.query("what powers the suit reactor", top_k=1)
        assert results[0].text.startswith("the arc reactor")
        await store.delete(ids)
        assert await store.count() == 0

    async def test_metadata_filter(self, tmp_path) -> None:
        store = LocalVectorStore(HashingEmbedder(), tmp_path / "vec.json")
        await store.add(["alpha beta"], [{"kind": "a"}])
        await store.add(["alpha gamma"], [{"kind": "b"}])
        results = await store.query("alpha", top_k=5, where={"kind": "b"})
        assert len(results) == 1
        assert results[0].metadata["kind"] == "b"

    async def test_persistence(self, tmp_path) -> None:
        path = tmp_path / "vec.json"
        store = LocalVectorStore(HashingEmbedder(), path)
        await store.add(["persistent memory record"])
        reloaded = LocalVectorStore(HashingEmbedder(), path)
        assert await reloaded.count() == 1


class TestRag:
    def test_chunking_respects_size_and_overlap(self) -> None:
        text = " ".join(f"word{i}" for i in range(500))
        chunks = chunk_text(text, chunk_size=200, overlap=50)
        assert all(len(c) <= 220 for c in chunks)
        assert len(chunks) > 2

    def test_chunking_small_text(self) -> None:
        assert chunk_text("short", chunk_size=100) == ["short"]
        assert chunk_text("", chunk_size=100) == []

    async def test_index_and_retrieve_with_citation(self, tmp_path) -> None:
        store = LocalVectorStore(HashingEmbedder(), tmp_path / "vec.json")
        rag = RagPipeline(store, chunk_size=200, chunk_overlap=20, top_k=2)
        await rag.index_text(
            "JARVIS runs on a modular multi-agent architecture with a model router.",
            source="architecture.md",
        )
        context = await rag.build_context("what architecture does JARVIS use")
        assert "architecture.md" in context
        assert "[1]" in context


class TestMemoryManager:
    async def test_turns_archived_and_recalled(self, config: JarvisConfig) -> None:
        long_term = LongTermMemory(config.data_dir / "mm.db")
        await long_term.open()
        store = LocalVectorStore(HashingEmbedder())
        manager = MemoryManager(config, long_term, store, RagPipeline(store))
        manager.short_term.max_messages = 2

        await manager.add_turn(Message.user("I am building an arc reactor in my garage"))
        await manager.add_turn(Message.assistant("Noted, Sir. A bold project."))
        await manager.add_turn(Message.user("Remind me to order palladium"))
        # First turn was evicted into the vector store as an episode.
        assert await store.count() >= 1
        await manager.remember("User's project: arc reactor", category="project")
        recall = await manager.recall("arc reactor project")
        assert "arc reactor" in recall
        stats = await manager.stats()
        assert stats["facts"] == 1
        await long_term.close()
