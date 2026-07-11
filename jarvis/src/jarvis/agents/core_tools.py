"""Core tools available to every JARVIS installation (no optional deps)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from jarvis.agents.tools import ToolRegistry
from jarvis.core.security import PythonSandbox
from jarvis.memory.manager import MemoryManager


def register_core_tools(
    tools: ToolRegistry,
    memory: MemoryManager,
    sandbox: PythonSandbox,
) -> None:
    """Register memory, RAG, sandbox and utility tools."""

    # -- memory ---------------------------------------------------------------

    async def remember(content: str, category: str = "general") -> str:
        fact_id = await memory.remember(content, category=category, source="agent")
        return f"Stored fact #{fact_id}"

    tools.register_function(
        "memory_remember",
        "Store a durable fact about the user or their world in long-term memory.",
        remember,
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The fact to remember"},
                "category": {
                    "type": "string",
                    "description": "Category, e.g. preference, project, person, general",
                },
            },
            "required": ["content"],
        },
        tags={"memory"},
    )

    async def recall(query: str) -> str:
        result = await memory.recall(query)
        return result or "No stored memories match this query."

    tools.register_function(
        "memory_recall",
        "Search long-term memory (facts, profile, past conversations) for relevant information.",
        recall,
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to look for"}},
            "required": ["query"],
        },
        tags={"memory", "rag"},
    )

    async def update_profile(key: str, value: str) -> str:
        await memory.update_profile(key, value)
        return f"Profile updated: {key}"

    tools.register_function(
        "memory_update_profile",
        "Set a user profile attribute (name, location, language, preferences, ...).",
        update_profile,
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["key", "value"],
        },
        tags={"memory"},
    )

    async def list_open_tasks() -> Any:
        items = await memory.long_term.list_tasks()
        return [
            {"id": t.id, "title": t.title, "details": t.details, "due_at": t.due_at}
            for t in items
        ]

    tools.register_function(
        "tasks_list",
        "List the user's open tasks and reminders.",
        list_open_tasks,
        tags={"tasks", "memory"},
    )

    async def add_task(title: str, details: str = "", due_at: str = "") -> str:
        task_id = await memory.long_term.add_task(title, details, due_at or None)
        return f"Task #{task_id} created"

    tools.register_function(
        "tasks_add",
        "Create a task or reminder for the user. due_at is an ISO datetime, optional.",
        add_task,
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "details": {"type": "string"},
                "due_at": {"type": "string", "description": "ISO 8601 due time, optional"},
            },
            "required": ["title"],
        },
        tags={"tasks", "memory"},
    )

    async def complete_task(task_id: int) -> str:
        done = await memory.long_term.complete_task(task_id)
        return f"Task #{task_id} completed" if done else f"No open task #{task_id}"

    tools.register_function(
        "tasks_complete",
        "Mark a task or reminder as done.",
        complete_task,
        parameters={
            "type": "object",
            "properties": {"task_id": {"type": "integer"}},
            "required": ["task_id"],
        },
        tags={"tasks", "memory"},
    )

    # -- RAG -----------------------------------------------------------------

    async def rag_index(text: str, source: str) -> str:
        count = await memory.rag.index_text(text, source=source)
        return f"Indexed {count} chunks from {source}"

    tools.register_function(
        "rag_index_text",
        "Add a document/text to the knowledge base for later retrieval.",
        rag_index,
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "source": {"type": "string", "description": "Name/URL/path identifying the text"},
            },
            "required": ["text", "source"],
        },
        tags={"rag", "memory"},
    )

    async def rag_search(query: str) -> str:
        context = await memory.rag.build_context(query)
        return context or "The knowledge base has no matching content."

    tools.register_function(
        "rag_search",
        "Retrieve relevant passages from the indexed knowledge base, with sources.",
        rag_search,
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        tags={"rag", "search"},
    )

    # -- code sandbox -------------------------------------------------------------

    async def run_python(code: str) -> Any:
        return await sandbox.run(code)

    tools.register_function(
        "run_python",
        "Execute a Python snippet in an isolated sandbox and return stdout/stderr/exit_code.",
        run_python,
        parameters={
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python source to run"}},
            "required": ["code"],
        },
        tags={"code"},
        capability="code.execute",
    )

    # -- utilities ----------------------------------------------------------------

    def current_datetime() -> str:
        return datetime.now().astimezone().isoformat()

    tools.register_function(
        "current_datetime",
        "Get the current local date and time (ISO 8601).",
        current_datetime,
        tags={"utility", "tasks"},
    )
