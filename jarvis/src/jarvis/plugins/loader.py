"""Plugin discovery, loading and hot reload.

Layout of a local plugin::

    plugins/
      weather/
        plugin.py      # defines `class WeatherPlugin(Plugin)` or `plugin = ...`
        plugin.yaml    # optional manifest override

Hot reload watches the plugin directories with ``watchfiles`` and reloads a
plugin whenever one of its files changes.
"""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from jarvis.core.errors import PluginError
from jarvis.core.logging import get_logger
from jarvis.plugins.api import Plugin, PluginContext, PluginManifest

logger = get_logger("plugins.loader")


@dataclass(slots=True)
class LoadedPlugin:
    name: str
    path: Path
    instance: Plugin
    context: PluginContext


class PluginLoader:
    """Loads plugin directories and supports hot reload."""

    def __init__(self, context_factory, directories: list[Path]) -> None:
        """``context_factory(name) -> PluginContext`` builds a fresh context per plugin."""
        self._context_factory = context_factory
        self._directories = list(directories)
        self._loaded: dict[str, LoadedPlugin] = {}
        self._watch_task: asyncio.Task | None = None

    @property
    def loaded(self) -> dict[str, LoadedPlugin]:
        return dict(self._loaded)

    # -- discovery / loading ------------------------------------------------------

    def discover(self) -> list[Path]:
        found: list[Path] = []
        for directory in self._directories:
            if not directory.is_dir():
                continue
            for entry in sorted(directory.iterdir()):
                if entry.is_dir() and (entry / "plugin.py").is_file():
                    found.append(entry)
        return found

    async def load_all(self) -> list[str]:
        names: list[str] = []
        for path in self.discover():
            try:
                names.append(await self.load(path))
            except PluginError as exc:
                logger.error("Skipping plugin at %s: %s", path, exc.message)
        return names

    async def load(self, path: Path) -> str:
        """Load (or replace) the plugin living at *path*; returns its name."""
        instance = self._instantiate(path)
        manifest = self._resolve_manifest(instance, path)
        name = manifest.name

        if name in self._loaded:
            await self.unload(name)

        context = self._context_factory(name)
        context._plugin_name = name
        try:
            await instance.setup(context)
        except Exception as exc:
            context._teardown()
            raise PluginError(f"Plugin '{name}' setup failed: {exc}", cause=exc) from exc

        self._loaded[name] = LoadedPlugin(name=name, path=path, instance=instance, context=context)
        logger.info("Loaded plugin '%s' v%s from %s", name, manifest.version, path)
        return name

    def _instantiate(self, path: Path) -> Plugin:
        module_file = path / "plugin.py"
        if not module_file.is_file():
            raise PluginError(f"No plugin.py in {path}")
        module_name = f"jarvis_plugin_{path.name}"
        # Drop any previously imported version so edits take effect.
        for key in [k for k in sys.modules if k == module_name or k.startswith(module_name + ".")]:
            del sys.modules[key]
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec is None or spec.loader is None:
            raise PluginError(f"Cannot create import spec for {module_file}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            raise PluginError(f"Plugin at {path} failed to import: {exc}", cause=exc) from exc

        candidate = getattr(module, "plugin", None)
        if isinstance(candidate, Plugin):
            return candidate
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Plugin) and obj is not Plugin and obj.__module__ == module_name:
                return obj()
        raise PluginError(f"{module_file} defines no Plugin subclass or 'plugin' instance")

    def _resolve_manifest(self, instance: Plugin, path: Path) -> PluginManifest:
        manifest = instance.manifest
        yaml_file = path / "plugin.yaml"
        if yaml_file.is_file():
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                manifest = PluginManifest(**{**manifest.model_dump(), **data})
                instance.manifest = manifest
        if manifest.name == "unnamed":
            manifest = manifest.model_copy(update={"name": path.name})
            instance.manifest = manifest
        return manifest

    async def unload(self, name: str) -> bool:
        loaded = self._loaded.pop(name, None)
        if loaded is None:
            return False
        try:
            await loaded.instance.teardown()
        except Exception:
            logger.exception("Plugin '%s' teardown failed", name)
        loaded.context._teardown()
        logger.info("Unloaded plugin '%s'", name)
        return True

    async def reload(self, name: str) -> str:
        loaded = self._loaded.get(name)
        if loaded is None:
            raise PluginError(f"Plugin '{name}' is not loaded")
        return await self.load(loaded.path)

    async def unload_all(self) -> None:
        for name in list(self._loaded):
            await self.unload(name)
        self.stop_watching()

    # -- hot reload ---------------------------------------------------------------

    def start_watching(self) -> None:
        """Begin watching plugin directories; changed plugins reload automatically."""
        if self._watch_task is not None:
            return
        directories = [str(d) for d in self._directories if d.is_dir()]
        if not directories:
            return
        self._watch_task = asyncio.get_running_loop().create_task(self._watch(directories))

    def stop_watching(self) -> None:
        if self._watch_task is not None:
            self._watch_task.cancel()
            self._watch_task = None

    async def _watch(self, directories: list[str]) -> None:
        from watchfiles import awatch

        logger.info("Hot reload watching: %s", ", ".join(directories))
        try:
            async for changes in awatch(*directories):
                touched_dirs = {Path(changed_path) for _, changed_path in changes}
                for loaded in list(self._loaded.values()):
                    if any(loaded.path in p.parents or p == loaded.path for p in touched_dirs):
                        logger.info("Change detected; reloading plugin '%s'", loaded.name)
                        try:
                            await self.load(loaded.path)
                        except PluginError as exc:
                            logger.error("Hot reload of '%s' failed: %s", loaded.name, exc.message)
                # Newly created plugins get picked up too.
                for path in self.discover():
                    if not any(lp.path == path for lp in self._loaded.values()):
                        try:
                            await self.load(path)
                        except PluginError as exc:
                            logger.error("Loading new plugin at %s failed: %s", path, exc.message)
        except asyncio.CancelledError:
            pass
