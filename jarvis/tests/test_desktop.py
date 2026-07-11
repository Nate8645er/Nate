"""Tests for the desktop subsystem (core dependencies + psutil only)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import jarvis.desktop
from jarvis.agents.tools import ToolRegistry
from jarvis.core.config import JarvisConfig
from jarvis.core.container import ServiceContainer
from jarvis.core.errors import DesktopError
from jarvis.core.events import EventBus
from jarvis.core.security import PermissionManager
from jarvis.desktop import apps, terminal, winapi
from jarvis.desktop.files import FileManager

EXPECTED_DESKTOP_TOOLS = {
    "files_read",
    "files_write",
    "files_delete",
    "files_move",
    "files_list",
    "files_search",
    "office_read_pdf",
    "office_read_excel",
    "office_write_excel",
    "office_read_word",
    "office_write_word",
    "office_read_powerpoint",
    "office_write_powerpoint",
    "app_launch",
    "app_close",
    "processes_list",
    "mouse_move",
    "mouse_click",
    "keyboard_type",
    "keyboard_hotkey",
    "terminal_run",
    "window_focus",
    "window_active",
}


@pytest.fixture()
def sandbox_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> JarvisConfig:
    """Config with a data dir and one allowed directory, both under tmp_path."""
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path / "data"))
    (tmp_path / "sandbox").mkdir()
    config = JarvisConfig(
        desktop={"enabled": True, "allowed_directories": [str(tmp_path / "sandbox")]}
    )
    config.ensure_dirs()
    return config


def make_stub_app(config: JarvisConfig) -> SimpleNamespace:
    """A minimal JarvisApp stand-in satisfying the register() contract."""
    permissions = PermissionManager(config)
    return SimpleNamespace(
        config=config,
        permissions=permissions,
        tools=ToolRegistry(permissions),
        events=EventBus(),
        container=ServiceContainer(),
    )


# -- FileManager sandbox ------------------------------------------------------


class TestFileManagerSandbox:
    async def test_write_read_roundtrip(self, sandbox_config: JarvisConfig, tmp_path: Path):
        manager = FileManager(sandbox_config)
        target = tmp_path / "sandbox" / "notes" / "hello.txt"
        await manager.write_text(str(target), "hello world")
        assert await manager.read_text(str(target)) == "hello world"

    async def test_append(self, sandbox_config: JarvisConfig, tmp_path: Path):
        manager = FileManager(sandbox_config)
        target = tmp_path / "sandbox" / "log.txt"
        await manager.append_text(str(target), "one")
        await manager.append_text(str(target), " two")
        assert target.read_text() == "one two"

    async def test_outside_path_blocked(self, sandbox_config: JarvisConfig, tmp_path: Path):
        manager = FileManager(sandbox_config)
        with pytest.raises(DesktopError):
            await manager.read_text(str(tmp_path / "outside.txt"))

    async def test_traversal_blocked(self, sandbox_config: JarvisConfig, tmp_path: Path):
        manager = FileManager(sandbox_config)
        with pytest.raises(DesktopError):
            await manager.write_text(str(tmp_path / "sandbox" / ".." / "escape.txt"), "x")

    async def test_relative_path_resolves_into_first_root(
        self, sandbox_config: JarvisConfig, tmp_path: Path
    ):
        manager = FileManager(sandbox_config)
        await manager.write_text("relative.txt", "data")
        assert (tmp_path / "sandbox" / "relative.txt").read_text() == "data"

    async def test_delete_moves_to_trash(self, sandbox_config: JarvisConfig, tmp_path: Path):
        manager = FileManager(sandbox_config)
        target = tmp_path / "sandbox" / "doomed.txt"
        target.write_text("bye")
        trash_path = Path(await manager.delete(str(target)))
        assert not target.exists()
        assert trash_path.is_file()
        assert trash_path.read_text() == "bye"
        assert trash_path.is_relative_to(sandbox_config.data_dir / ".jarvis-trash")

    async def test_delete_missing_file(self, sandbox_config: JarvisConfig, tmp_path: Path):
        manager = FileManager(sandbox_config)
        with pytest.raises(DesktopError):
            await manager.delete(str(tmp_path / "sandbox" / "nope.txt"))

    async def test_list_dir_and_search(self, sandbox_config: JarvisConfig, tmp_path: Path):
        manager = FileManager(sandbox_config)
        base = tmp_path / "sandbox"
        (base / "a.py").write_text("needle in code")
        (base / "b.py").write_text("nothing here")
        entries = await manager.list_dir(str(base))
        names = {entry["name"] for entry in entries}
        assert {"a.py", "b.py"} <= names
        assert all({"name", "type", "size", "modified"} <= set(e) for e in entries)
        hits = await manager.search(str(base), pattern="*.py", content="needle")
        assert hits == [str(base / "a.py")]

    def test_defaults_to_home_when_unconfigured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path / "data"))
        manager = FileManager(JarvisConfig())
        assert manager.allowed_directories == (Path.home().resolve(),)


# -- terminal -------------------------------------------------------------------


class TestTerminal:
    async def test_echo_roundtrip(self):
        result = await terminal.run_command("echo jarvis-test")
        assert result["exit_code"] == 0
        assert "jarvis-test" in result["stdout"]

    async def test_stderr_and_exit_code(self):
        result = await terminal.run_command("echo oops >&2; exit 3")
        assert result["exit_code"] == 3
        assert "oops" in result["stderr"]

    async def test_timeout(self):
        result = await terminal.run_command("sleep 5", timeout=0.3)
        assert result["exit_code"] == -1
        assert "timed out" in result["stderr"]

    async def test_empty_command_rejected(self):
        with pytest.raises(DesktopError):
            await terminal.run_command("   ")

    async def test_missing_cwd_rejected(self, tmp_path: Path):
        with pytest.raises(DesktopError):
            await terminal.run_command("echo hi", cwd=str(tmp_path / "does-not-exist"))


# -- apps / processes --------------------------------------------------------------


class TestApps:
    def test_list_processes_shape(self):
        processes = apps.list_processes()
        assert isinstance(processes, list)
        assert processes, "expected at least one running process"
        entry = processes[0]
        assert set(entry) == {"pid", "name", "memory_mb"}
        assert isinstance(entry["pid"], int)
        assert isinstance(entry["name"], str)

    def test_list_processes_filter(self):
        assert apps.list_processes("definitely-not-a-process-name-xyz") == []

    def test_launch_unknown_executable(self):
        with pytest.raises(DesktopError):
            apps.launch_app("definitely-not-a-real-binary-xyz")

    def test_close_unknown_process(self):
        with pytest.raises(DesktopError):
            apps.close_app("definitely-not-a-process-name-xyz")


# -- winapi ------------------------------------------------------------------------


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows behaviour")
def test_winapi_raises_on_non_windows():
    with pytest.raises(DesktopError, match="only available on Windows"):
        winapi.get_active_window_title()


# -- register() ---------------------------------------------------------------------


class TestRegister:
    def test_register_exposes_tools(self, sandbox_config: JarvisConfig):
        app = make_stub_app(sandbox_config)
        jarvis.desktop.register(app)
        names = {tool.name for tool in app.tools.all()}
        assert names >= EXPECTED_DESKTOP_TOOLS
        assert app.container.has(FileManager)

    def test_capabilities_assigned(self, sandbox_config: JarvisConfig):
        app = make_stub_app(sandbox_config)
        jarvis.desktop.register(app)
        assert app.tools.get("files_write").capability == "files.write"
        assert app.tools.get("files_move").capability == "files.write"
        assert app.tools.get("files_delete").capability == "files.delete"
        assert app.tools.get("terminal_run").capability == "desktop.terminal"
        assert app.tools.get("mouse_click").capability == "desktop.input"
        assert app.tools.get("app_launch").capability == "desktop.apps"
        assert app.tools.get("files_read").capability is None

    async def test_files_write_denied_by_default_policy(
        self, sandbox_config: JarvisConfig, tmp_path: Path
    ):
        app = make_stub_app(sandbox_config)
        jarvis.desktop.register(app)
        target = tmp_path / "sandbox" / "denied.txt"
        result = await app.tools.execute(
            "files_write", {"path": str(target), "content": "hi"}
        )
        assert result.startswith("Permission denied")
        assert not target.exists()

    async def test_files_read_allowed_without_confirmation(
        self, sandbox_config: JarvisConfig, tmp_path: Path
    ):
        app = make_stub_app(sandbox_config)
        jarvis.desktop.register(app)
        target = tmp_path / "sandbox" / "readme.txt"
        target.write_text("visible")
        result = await app.tools.execute("files_read", {"path": str(target)})
        assert result == "visible"

    async def test_files_read_outside_sandbox_is_error_string(
        self, sandbox_config: JarvisConfig, tmp_path: Path
    ):
        app = make_stub_app(sandbox_config)
        jarvis.desktop.register(app)
        result = await app.tools.execute("files_read", {"path": str(tmp_path / "nope.txt")})
        assert result.startswith("Error:")
        assert "outside the allowed directories" in result

    async def test_office_tool_reports_missing_dependency(self, sandbox_config: JarvisConfig):
        app = make_stub_app(sandbox_config)
        jarvis.desktop.register(app)
        result = await app.tools.execute("office_read_pdf", {"path": "anything.pdf"})
        assert result.startswith("Error:")
        assert "pypdf" in result
