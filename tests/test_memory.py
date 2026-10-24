from pathlib import Path

from jarvis.memory.manager import MemoryManager
from jarvis.memory.vector import NaiveVectorStore


async def test_short_and_long_term_roundtrip(tmp_path: Path):
    memory = MemoryManager(tmp_path, vector_backend="naive")
    await memory.observe("s1", "user", "Ich heiße Nate und mag Python")
    await memory.observe("s1", "assistant", "Hallo Nate!")

    recent = memory.short_term.recall("s1")
    assert [m.role for m in recent] == ["user", "assistant"]

    history = await memory.long_term.conversation("s1")
    assert len(history) == 2
    assert history[0]["content"].startswith("Ich heiße")
    memory.close()


async def test_facts_and_search(tmp_path: Path):
    memory = MemoryManager(tmp_path, vector_backend="naive")
    await memory.remember("lieblingssprache", "Python", kind="preference")
    await memory.remember("projekt", "JARVIS AI OS bauen", kind="project")

    facts = await memory.long_term.recall(query="Python")
    assert len(facts) == 1
    assert facts[0]["kind"] == "preference"

    hits = await memory.search("Python Sprache")
    assert hits and "Python" in hits[0]["text"]
    memory.close()


async def test_context_pack(tmp_path: Path):
    memory = MemoryManager(tmp_path, vector_backend="naive")
    await memory.remember("wohnort", "Zürich")
    await memory.observe("s1", "user", "Wie ist das Wetter bei mir?")
    pack = await memory.context_pack("s1", "Wetter")
    assert pack["recent"][-1]["content"] == "Wie ist das Wetter bei mir?"
    assert any(f["subject"] == "wohnort" for f in pack["facts"])
    memory.close()


async def test_naive_vector_ranking():
    store = NaiveVectorStore()
    await store.add("Rechnungen und Steuern für das Büro")
    await store.add("Python Programmierung und Software")
    hits = await store.search("Software in Python schreiben", limit=1)
    assert "Python" in hits[0]["text"]
