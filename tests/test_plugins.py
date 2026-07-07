import json
from pathlib import Path

from jarvis.kernel import Kernel

PLUGIN_CODE = '''
from jarvis.core.approvals import Risk
from jarvis.skills.base import Skill

async def ping() -> str:
    return "pong"

def setup(kernel):
    kernel.skills.register(Skill(
        name="ping", description="test", category="general",
        risk=Risk.READ, func=ping, parameters={},
    ))
'''


def make_plugin(plugins_dir: Path, plugin_id: str = "testplug", version: str = "1.0.0") -> Path:
    plugin_dir = plugins_dir / plugin_id
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.json").write_text(json.dumps({
        "id": plugin_id, "name": "Test Plugin", "version": version,
        "description": "Testet das Plugin-System", "entry": "plugin.py",
    }))
    (plugin_dir / "plugin.py").write_text(PLUGIN_CODE)
    return plugin_dir


async def test_discover_and_load(kernel: Kernel):
    make_plugin(kernel.settings.plugins_dir)
    found = kernel.plugins.discover()
    assert [p.id for p in found] == ["testplug"]

    await kernel.plugins.load("testplug")
    assert kernel.plugins.plugins["testplug"].loaded
    assert await kernel.skills.invoke("ping") == "pong"
    # Skill is attributed to the plugin, so disable removes it.
    assert kernel.skills.get("ping").source == "testplug"


async def test_disable_removes_skills(kernel: Kernel):
    make_plugin(kernel.settings.plugins_dir)
    kernel.plugins.discover()
    await kernel.plugins.load("testplug")

    await kernel.plugins.set_enabled("testplug", False)
    assert kernel.skills.get("ping") is None
    assert not kernel.plugins.plugins["testplug"].loaded

    await kernel.plugins.set_enabled("testplug", True)
    assert kernel.skills.get("ping") is not None


async def test_disabled_state_persisted(kernel: Kernel):
    make_plugin(kernel.settings.plugins_dir)
    kernel.plugins.discover()
    await kernel.plugins.load("testplug")
    await kernel.plugins.set_enabled("testplug", False)

    # A fresh manager (fresh boot) must remember the choice.
    from jarvis.plugins.manager import PluginManager

    fresh = PluginManager(kernel, kernel.settings.plugins_dir)
    fresh.discover()
    assert fresh.plugins["testplug"].enabled is False


async def test_version_update_via_reload(kernel: Kernel):
    plugin_dir = make_plugin(kernel.settings.plugins_dir, version="1.0.0")
    kernel.plugins.discover()
    await kernel.plugins.load("testplug")
    assert kernel.plugins.plugins["testplug"].version == "1.0.0"

    manifest = json.loads((plugin_dir / "plugin.json").read_text())
    manifest["version"] = "2.0.0"
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest))

    await kernel.plugins.reload("testplug")
    assert kernel.plugins.plugins["testplug"].version == "2.0.0"
    assert await kernel.skills.invoke("ping") == "pong"


async def test_invalid_manifest_ignored(kernel: Kernel):
    bad = kernel.settings.plugins_dir / "broken"
    bad.mkdir(parents=True)
    (bad / "plugin.json").write_text("{ not json")
    found = kernel.plugins.discover()
    assert found == []
