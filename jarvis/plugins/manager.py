"""Plugin system.

A plugin is a directory inside the plugins folder:

    plugins/
      weather/
        plugin.json     # manifest: id, name, version, description, entry
        plugin.py       # entry module exposing setup(kernel) -> None

Lifecycle:
  * discover  — scan the plugins dir for manifests (auto-detected)
  * load      — import the entry module, call setup(kernel); skills the
                plugin registers are tagged with its id
  * disable   — unload + remember the choice (persisted in state.json)
  * update    — replace the directory, then reload() picks up the new version

Versions live in the manifest; state (enabled/disabled) is persisted next
to the plugins so a restart keeps your choices.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jarvis.kernel import Kernel

log = logging.getLogger(__name__)

MANIFEST = "plugin.json"


@dataclass
class Plugin:
    id: str
    name: str
    version: str
    description: str
    path: Path
    entry: str = "plugin.py"
    loaded: bool = False
    enabled: bool = True
    error: str = ""
    module: Any = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "path": str(self.path),
            "loaded": self.loaded,
            "enabled": self.enabled,
            "error": self.error,
        }


class PluginManager:
    def __init__(self, kernel: "Kernel", plugins_dir: Path) -> None:
        self.kernel = kernel
        self.plugins_dir = plugins_dir
        self.plugins: dict[str, Plugin] = {}
        self._state_file = plugins_dir / ".state.json"

    # --- state persistence ---

    def _load_state(self) -> dict[str, Any]:
        try:
            return json.loads(self._state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_state(self) -> None:
        state = {pid: {"enabled": p.enabled} for pid, p in self.plugins.items()}
        try:
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except OSError:
            log.warning("Could not persist plugin state")

    # --- discovery & lifecycle ---

    def discover(self) -> list[Plugin]:
        """Scan the plugins directory; returns newly found plugins."""
        found: list[Plugin] = []
        if not self.plugins_dir.is_dir():
            return found
        state = self._load_state()
        for manifest_path in sorted(self.plugins_dir.glob(f"*/{MANIFEST}")):
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                plugin = Plugin(
                    id=data["id"],
                    name=data.get("name", data["id"]),
                    version=str(data.get("version", "0.0.0")),
                    description=data.get("description", ""),
                    path=manifest_path.parent,
                    entry=data.get("entry", "plugin.py"),
                    enabled=state.get(data["id"], {}).get("enabled", True),
                )
            except (KeyError, json.JSONDecodeError) as exc:
                log.warning("Invalid plugin manifest %s: %s", manifest_path, exc)
                continue
            if plugin.id not in self.plugins:
                self.plugins[plugin.id] = plugin
                found.append(plugin)
        return found

    async def load(self, plugin_id: str) -> Plugin:
        plugin = self.plugins[plugin_id]
        if plugin.loaded:
            return plugin
        if not plugin.enabled:
            raise PermissionError(f"Plugin disabled: {plugin_id}")
        entry_path = plugin.path / plugin.entry
        try:
            spec = importlib.util.spec_from_file_location(
                f"jarvis_plugin_{plugin.id}", entry_path
            )
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            before = {s.name for s in self.kernel.skills.all()}
            if hasattr(module, "setup"):
                result = module.setup(self.kernel)
                if hasattr(result, "__await__"):
                    await result
            # Adopt decorator-declared skills and tag everything new.
            self.kernel.skills.collect_pending()
            for s in self.kernel.skills.all():
                if s.name not in before and s.source == "builtin":
                    s.source = plugin.id

            plugin.module = module
            plugin.loaded = True
            plugin.error = ""
            await self.kernel.bus.publish("plugin.loaded", plugin.to_dict(), source="plugins")
        except Exception as exc:  # noqa: BLE001 - plugin errors must not kill boot
            plugin.error = str(exc)
            log.exception("Failed to load plugin %s", plugin_id)
            raise
        return plugin

    async def load_all(self) -> int:
        self.discover()
        count = 0
        for plugin in self.plugins.values():
            if plugin.enabled and not plugin.loaded:
                try:
                    await self.load(plugin.id)
                    count += 1
                except Exception:  # noqa: BLE001
                    continue
        self._save_state()
        return count

    async def unload(self, plugin_id: str) -> None:
        plugin = self.plugins[plugin_id]
        if not plugin.loaded:
            return
        if plugin.module is not None and hasattr(plugin.module, "teardown"):
            result = plugin.module.teardown(self.kernel)
            if hasattr(result, "__await__"):
                await result
        removed = self.kernel.skills.unregister_source(plugin_id)
        sys.modules.pop(f"jarvis_plugin_{plugin.id}", None)
        plugin.module = None
        plugin.loaded = False
        await self.kernel.bus.publish(
            "plugin.unloaded", {"id": plugin_id, "skills_removed": removed}, source="plugins"
        )

    async def set_enabled(self, plugin_id: str, enabled: bool) -> Plugin:
        plugin = self.plugins[plugin_id]
        plugin.enabled = enabled
        if not enabled and plugin.loaded:
            await self.unload(plugin_id)
        elif enabled and not plugin.loaded:
            await self.load(plugin_id)
        self._save_state()
        return plugin

    async def reload(self, plugin_id: str) -> Plugin:
        """Pick up a new version of the plugin (after an update)."""
        await self.unload(plugin_id)
        # Re-read the manifest so version bumps are reflected.
        manifest_path = self.plugins[plugin_id].path / MANIFEST
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.plugins[plugin_id].version = str(data.get("version", "0.0.0"))
        self.plugins[plugin_id].description = data.get("description", "")
        return await self.load(plugin_id)

    async def install_from_path(self, source: Path) -> Plugin:
        """Install a plugin by copying its directory into the plugins folder."""
        import shutil

        manifest = source / MANIFEST
        data = json.loads(manifest.read_text(encoding="utf-8"))
        target = self.plugins_dir / data["id"]
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        self.plugins.pop(data["id"], None)
        self.discover()
        plugin = await self.load(data["id"])
        self._save_state()
        return plugin

    def status(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self.plugins.values()]
