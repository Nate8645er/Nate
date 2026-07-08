"""Automatisches Laden aller Plugins aus jarvis/plugins/."""

import importlib
import inspect
import logging
import pkgutil

import jarvis.plugins
from jarvis.plugins.base import JarvisPlugin

logger = logging.getLogger("jarvis.plugins")

# Module, die keine Plugins sind
_SKIP_MODULES = {"base", "loader"}


class PluginManager:
    """Findet, lädt und verwaltet alle Plugins."""

    def __init__(self):
        self.plugins: list[JarvisPlugin] = []
        #: Befehl -> Plugin-Instanz
        self.command_map: dict[str, JarvisPlugin] = {}

    def load_plugins(self) -> None:
        """Durchsucht jarvis/plugins/ und lädt alle JarvisPlugin-Klassen."""
        for module_info in pkgutil.iter_modules(jarvis.plugins.__path__):
            if module_info.name in _SKIP_MODULES:
                continue
            try:
                module = importlib.import_module(
                    f"jarvis.plugins.{module_info.name}"
                )
            except Exception as e:  # Fehler in einem Plugin stoppt Jarvis nicht
                logger.error(
                    "Plugin-Modul '%s' konnte nicht geladen werden: %s",
                    module_info.name, e,
                )
                continue

            for _, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, JarvisPlugin) and cls is not JarvisPlugin:
                    self._register(cls)

        logger.info(
            "%d Plugin(s) geladen: %s",
            len(self.plugins),
            ", ".join(p.name for p in self.plugins) or "keine",
        )

    def _register(self, cls: type) -> None:
        try:
            plugin = cls()
        except Exception as e:
            logger.error("Plugin '%s' konnte nicht initialisiert werden: %s",
                         cls.__name__, e)
            return
        self.plugins.append(plugin)
        for command in plugin.commands:
            if command in self.command_map:
                logger.warning(
                    "Befehl /%s ist doppelt vergeben - '%s' überschreibt ihn.",
                    command, plugin.name,
                )
            self.command_map[command] = plugin

    def handle(self, command: str, args: str) -> str | None:
        """Führt einen Plugin-Befehl aus. None, wenn kein Plugin zuständig ist."""
        plugin = self.command_map.get(command)
        if plugin is None:
            return None
        try:
            return plugin.execute(command, args)
        except Exception as e:
            logger.error("Fehler im Plugin '%s': %s", plugin.name, e)
            return f"Das Plugin '{plugin.name}' hat einen Fehler gemeldet: {e}"

    def overview(self) -> str:
        """Übersicht aller Plugins und ihrer Befehle für /plugins."""
        if not self.plugins:
            return "Keine Plugins geladen."
        lines = []
        for plugin in self.plugins:
            lines.append(f"• {plugin.name} - {plugin.description}")
            for command, desc in plugin.commands.items():
                lines.append(f"    /{command} - {desc}")
        return "\n".join(lines)
