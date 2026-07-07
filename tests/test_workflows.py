import pytest

from jarvis.kernel import Kernel
from jarvis.workflows.engine import Workflow


async def test_skill_steps_with_templating(kernel: Kernel, tmp_path):
    target = tmp_path / "out.txt"
    kernel.workflows.register(Workflow(
        name="write-stats",
        steps=[
            {"name": "stats", "skill": "system_stats", "args": {}},
            {"name": "save", "skill": "write_file",
             "args": {"path": str(target), "content": "Stats: {{steps.stats}}"}},
        ],
    ))
    record = await kernel.workflows.run("write-stats")
    assert record["status"] == "done"
    assert target.read_text().startswith("Stats: ")


async def test_agent_step(kernel: Kernel):
    kernel.workflows.register(Workflow(
        name="ask-ceo",
        steps=[{"name": "answer", "agent": "ceo", "goal": "Kurzer Statusbericht"}],
    ))
    record = await kernel.workflows.run("ask-ceo")
    assert record["status"] == "done"
    assert record["steps"]["answer"]


async def test_failed_step_marks_run_failed(kernel: Kernel):
    kernel.workflows.register(Workflow(
        name="broken",
        steps=[{"name": "x", "skill": "does_not_exist", "args": {}}],
    ))
    with pytest.raises(KeyError):
        await kernel.workflows.run("broken")
    run = next(iter(kernel.workflows.runs.values()))
    assert run["status"] == "failed"


async def test_unknown_workflow(kernel: Kernel):
    with pytest.raises(KeyError):
        await kernel.workflows.run("nope")
