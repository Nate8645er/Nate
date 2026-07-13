"""Plugin-System: zentrale Verwaltung, Autorisierung pro Team, dynamisches Laden.

Ein Plugin ist eine Klasse mit `name`, `description`, optional `allowed_teams`
(None = alle Teams autorisiert) und einer `run(action, **kwargs)`-Methode.
Neue Plugins: einfach eine .py-Datei in jarvis/plugins/ ablegen, die eine
Variable PLUGIN mit einer Plugin-Instanz exportiert.
"""

from __future__ import annotations

import ast
import importlib
import operator
import pkgutil
import time
from pathlib import Path
from typing import Any


class Plugin:
    name: str = "base"
    description: str = ""
    allowed_teams: list[str] | None = None  # None = alle

    def authorized(self, team: str) -> bool:
        return self.allowed_teams is None or team in self.allowed_teams

    def run(self, action: str, **kwargs: Any) -> Any:  # pragma: no cover - Interface
        raise NotImplementedError

    def status(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description,
                "allowed_teams": self.allowed_teams or "alle", "ok": True}


# ---------------------------------------------------------------------------
# Eingebaute Plugins
# ---------------------------------------------------------------------------

class SystemInfoPlugin(Plugin):
    name = "system"
    description = "CPU-, RAM- und Plattform-Informationen"

    def run(self, action: str = "info", **kwargs: Any) -> Any:
        import platform

        import psutil

        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count": psutil.cpu_count(),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_available_mb": psutil.virtual_memory().available // 1_048_576,
            "platform": platform.platform(),
        }


class FilesPlugin(Plugin):
    name = "files"
    description = "Dateien im JARVIS-Arbeitsbereich lesen, schreiben, auflisten"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _safe(self, rel: str) -> Path:
        p = (self.workspace / rel).resolve()
        if not str(p).startswith(str(self.workspace.resolve())):
            raise PermissionError("Zugriff außerhalb des Arbeitsbereichs verweigert")
        return p

    def run(self, action: str, path: str = ".", content: str = "", **kwargs: Any) -> Any:
        if action == "list":
            return sorted(str(p.relative_to(self.workspace)) for p in self._safe(path).glob("*"))
        if action == "read":
            return self._safe(path).read_text(encoding="utf-8")
        if action == "write":
            target = self._safe(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"geschrieben: {path} ({len(content)} Zeichen)"
        raise ValueError(f"Unbekannte Aktion: {action}")


class CalculatorPlugin(Plugin):
    name = "calc"
    description = "Sicherer Rechner (nur arithmetische Ausdrücke)"

    _OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
            ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
            ast.USub: operator.neg, ast.UAdd: operator.pos, ast.FloorDiv: operator.floordiv}

    def _eval(self, node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return self._eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in self._OPS:
            return self._OPS[type(node.op)](self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._OPS:
            return self._OPS[type(node.op)](self._eval(node.operand))
        raise ValueError("Nur arithmetische Ausdrücke erlaubt")

    def run(self, action: str = "eval", expression: str = "0", **kwargs: Any) -> Any:
        return self._eval(ast.parse(expression, mode="eval"))


class ClockPlugin(Plugin):
    name = "clock"
    description = "Datum, Uhrzeit, Zeitstempel"

    def run(self, action: str = "now", **kwargs: Any) -> Any:
        return {"iso": time.strftime("%Y-%m-%d %H:%M:%S"), "epoch": int(time.time())}


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class PluginManager:
    """Zentrale Registry. Agenten erhalten nur autorisierte Plugins."""

    def __init__(self, workspace: Path) -> None:
        self.plugins: dict[str, Plugin] = {}
        for plugin in (SystemInfoPlugin(), FilesPlugin(workspace / "files"),
                       CalculatorPlugin(), ClockPlugin()):
            self.plugins[plugin.name] = plugin
        self._load_external()

    def _load_external(self) -> None:
        """Lädt Zusatz-Plugins aus jarvis/plugins/*.py (Variable PLUGIN)."""
        pkg_dir = Path(__file__).resolve().parent.parent / "plugins"
        if not pkg_dir.is_dir():
            return
        for mod_info in pkgutil.iter_modules([str(pkg_dir)]):
            try:
                mod = importlib.import_module(f"jarvis.plugins.{mod_info.name}")
                plugin = getattr(mod, "PLUGIN", None)
                if isinstance(plugin, Plugin):
                    self.plugins[plugin.name] = plugin
            except Exception:  # defektes Plugin darf das System nicht stoppen
                continue

    def for_team(self, team: str) -> list[str]:
        return [name for name, p in self.plugins.items() if p.authorized(team)]

    def run(self, team: str, name: str, action: str, **kwargs: Any) -> Any:
        plugin = self.plugins.get(name)
        if plugin is None:
            raise KeyError(f"Plugin nicht gefunden: {name}")
        if not plugin.authorized(team):
            raise PermissionError(f"Team {team!r} ist für Plugin {name!r} nicht autorisiert")
        return plugin.run(action, **kwargs)

    def status(self) -> list[dict[str, Any]]:
        return [p.status() for p in self.plugins.values()]
