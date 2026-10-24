import asyncio

from jarvis.agents.base import AgentSpec, TaskStatus
from jarvis.kernel import Kernel


async def _wait_done(task, timeout=5.0):
    async with asyncio.timeout(timeout):
        while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            await asyncio.sleep(0.01)
    return task


async def test_company_staffed(kernel: Kernel):
    names = {a.spec.name for a in kernel.agents.all()}
    # A representative sample of the org chart:
    assert {"ceo", "coding", "research", "devops", "marketing", "memory"} <= names
    assert len(names) >= 19


async def test_agent_processes_task(kernel: Kernel):
    agent = kernel.agents.get("ceo")
    task = await agent.submit("Sag hallo")
    await _wait_done(task)
    assert task.status is TaskStatus.DONE
    assert task.result  # echo provider always answers


async def test_hire_and_fire(kernel: Kernel):
    kernel.company.hire("legal", "Legal Agent", "operations", "Verträge prüfen")
    assert kernel.agents.get("legal") is not None
    assert await kernel.company.fire("legal") is True
    assert kernel.agents.get("legal") is None


async def test_agents_work_concurrently(kernel: Kernel):
    a, b = kernel.agents.get("coding"), kernel.agents.get("research")
    t1 = await a.submit("Aufgabe A")
    t2 = await b.submit("Aufgabe B")
    await asyncio.gather(_wait_done(t1), _wait_done(t2))
    assert t1.status is TaskStatus.DONE and t2.status is TaskStatus.DONE


async def test_orchestrator_routes_explicit_mention(kernel: Kernel):
    task = await kernel.orchestrator.handle_utterance("@coding schreibe eine Funktion")
    await _wait_done(task)
    assert task.id in kernel.agents.get("coding").tasks


async def test_orchestrator_keyword_routing(kernel: Kernel):
    task = await kernel.orchestrator.handle_utterance("Bitte recherchiere das Thema KI")
    await _wait_done(task)
    assert task.id in kernel.agents.get("research").tasks


async def test_orchestrator_default_is_ceo(kernel: Kernel):
    task = await kernel.orchestrator.handle_utterance("Wie geht es dir?")
    await _wait_done(task)
    assert task.id in kernel.agents.get("ceo").tasks


async def test_failed_task_reports_error(kernel: Kernel):
    class Boom(Exception):
        pass

    spec = AgentSpec(name="bomber", title="Bomber")
    agent = kernel.agents.spawn(spec)

    async def broken_handle(task):
        raise Boom("kaputt")

    agent.handle = broken_handle
    task = await agent.submit("explodiere")
    await _wait_done(task)
    assert task.status is TaskStatus.FAILED
    assert "kaputt" in task.error
