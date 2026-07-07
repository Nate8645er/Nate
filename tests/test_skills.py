from pathlib import Path

import pytest

from jarvis.config import Settings
from jarvis.core.approvals import Risk
from jarvis.kernel import Kernel


async def test_builtin_skills_registered(kernel: Kernel):
    names = {s.name for s in kernel.skills.all()}
    assert {"list_files", "write_file", "web_search", "remember_fact",
            "create_reminder", "delegate", "run_command"} <= names


async def test_file_skills_roundtrip(kernel: Kernel, tmp_path: Path):
    path = tmp_path / "hello.txt"
    await kernel.skills.invoke("write_file", path=str(path), content="hallo jarvis")
    text = await kernel.skills.invoke("read_file", path=str(path))
    assert text == "hallo jarvis"
    listing = await kernel.skills.invoke("list_files", path=str(tmp_path))
    assert any(entry["name"] == "hello.txt" for entry in listing)


async def test_disabled_skill_rejected(kernel: Kernel):
    kernel.skills.set_enabled("system_stats", False)
    with pytest.raises(PermissionError):
        await kernel.skills.invoke("system_stats")
    kernel.skills.set_enabled("system_stats", True)
    stats = await kernel.skills.invoke("system_stats")
    assert "platform" in stats


async def test_unknown_skill(kernel: Kernel):
    with pytest.raises(KeyError):
        await kernel.skills.invoke("does_not_exist")


async def test_risky_skill_denied_without_approval(test_settings: Settings, tmp_path: Path):
    # threshold=1: every WRITE+ needs approval; nobody answers -> deny.
    test_settings.approval_threshold = 1
    test_settings.approval_timeout_seconds = 0.05
    k = Kernel(test_settings)
    await k.start()
    try:
        with pytest.raises(PermissionError):
            await k.skills.invoke("write_file", path=str(tmp_path / "x"), content="nope")
        assert not (tmp_path / "x").exists()
    finally:
        await k.stop()


async def test_reminder_skill(kernel: Kernel):
    job = await kernel.skills.invoke("create_reminder", message="Tee kochen", in_minutes=0.001)
    assert job["kind"] == "reminder"
    event = await kernel.bus.wait_for("reminder.due", timeout=5)
    assert event.data["message"] == "Tee kochen"


async def test_delegate_skill(kernel: Kernel):
    result = await kernel.skills.invoke("delegate", agent="coding", goal="tu was")
    assert "delegiert an coding" in result
    result = await kernel.skills.invoke("delegate", agent="niemand", goal="x")
    assert "Unbekannter Agent" in result


async def test_skill_risk_levels_honest(kernel: Kernel):
    assert kernel.skills.get("delete_path").risk is Risk.CRITICAL
    assert kernel.skills.get("run_command").risk is Risk.SYSTEM
    assert kernel.skills.get("list_files").risk is Risk.READ
