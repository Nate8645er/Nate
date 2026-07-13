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


class TasksPlugin(Plugin):
    name = "aufgaben"
    description = "Aufgaben, Erinnerungen und To-dos verwalten (echte Liste)"

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[dict[str, Any]]:
        import json
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return []

    def _save(self, items: list[dict[str, Any]]) -> None:
        import json
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

    def run(self, action: str = "list", text: str = "", id: str = "0",
            faellig: str = "", **kwargs: Any) -> Any:
        items = self._load()
        if action == "add":
            if not text:
                raise ValueError("text= fehlt")
            item = {"id": (max((i["id"] for i in items), default=0) + 1),
                    "text": text, "faellig": faellig, "erledigt": False,
                    "erstellt": time.strftime("%Y-%m-%d %H:%M")}
            items.append(item); self._save(items)
            return f"Aufgabe #{item['id']} angelegt: {text}"
        if action == "done":
            for i in items:
                if i["id"] == int(id):
                    i["erledigt"] = True; self._save(items)
                    return f"Aufgabe #{id} erledigt."
            raise ValueError(f"Aufgabe #{id} nicht gefunden")
        if action == "list":
            offen = [i for i in items if not i["erledigt"]]
            return offen if offen else "Keine offenen Aufgaben."
        raise ValueError(f"Unbekannte Aktion: {action}")


class FinancePlugin(Plugin):
    """Echte Buchhaltung: dokumentiert nur, was der Benutzer selbst erfasst.

    Ehrlichkeits-Doktrin: dieses Plugin ERZEUGT kein Geld und simuliert
    keine Umsätze — es summiert ausschließlich manuell erfasste, reale
    Einnahmen und Ausgaben. Der Ziel-Ticker rechnet damit.
    """

    name = "finanzen"
    description = "Echte Einnahmen/Ausgaben dokumentieren (kein simuliertes Geld)"

    def __init__(self, db_path: Path) -> None:
        import sqlite3
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS ledger ("
                          " ts REAL, art TEXT, betrag REAL, notiz TEXT)")
        self.conn.commit()

    def run(self, action: str = "summe", betrag: str = "0", notiz: str = "", **kwargs: Any) -> Any:
        if action in ("einnahme", "ausgabe"):
            b = float(str(betrag).replace("'", "").replace(",", "."))
            if b <= 0:
                raise ValueError("betrag= muss positiv sein")
            self.conn.execute("INSERT INTO ledger VALUES (?,?,?,?)",
                              (time.time(), action, b, notiz))
            self.conn.commit()
            return f"{action} über {b:.2f} CHF erfasst ({notiz or 'ohne Notiz'})"
        if action == "summe":
            ein = self.conn.execute("SELECT COALESCE(SUM(betrag),0) FROM ledger WHERE art='einnahme'").fetchone()[0]
            aus = self.conn.execute("SELECT COALESCE(SUM(betrag),0) FROM ledger WHERE art='ausgabe'").fetchone()[0]
            n = self.conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
            return {"einnahmen": round(ein, 2), "ausgaben": round(aus, 2),
                    "saldo": round(ein - aus, 2), "eintraege": n}
        if action == "liste":
            rows = self.conn.execute(
                "SELECT ts, art, betrag, notiz FROM ledger ORDER BY ts DESC LIMIT 20").fetchall()
            return [{"zeit": time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)),
                     "art": art, "betrag": b, "notiz": notiz} for ts, art, b, notiz in rows]
        raise ValueError(f"Unbekannte Aktion: {action}")


class WebSearchPlugin(Plugin):
    name = "web"
    description = "Internet-Suche (DuckDuckGo)"

    def run(self, action: str = "suche", query: str = "", **kwargs: Any) -> Any:
        import html
        import re
        import urllib.parse
        import urllib.request
        if not query:
            raise ValueError("query= fehlt")
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (JARVIS)"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                page = resp.read().decode("utf-8", "ignore")
        except Exception as e:
            return f"Suche fehlgeschlagen ({type(e).__name__}) — Internetzugang prüfen."
        hits = re.findall(r'class="result__a"[^>]*>(.*?)</a>', page)[:5]
        clean = [html.unescape(re.sub(r"<[^>]+>", "", h)).strip() for h in hits]
        return clean or "Keine Treffer."


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class PluginManager:
    """Zentrale Registry. Agenten erhalten nur autorisierte Plugins."""

    def __init__(self, workspace: Path) -> None:
        self.plugins: dict[str, Plugin] = {}
        for plugin in (SystemInfoPlugin(), FilesPlugin(workspace / "files"),
                       CalculatorPlugin(), ClockPlugin(),
                       TasksPlugin(workspace / "aufgaben.json"),
                       FinancePlugin(workspace / "finanzen.db"),
                       WebSearchPlugin()):
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
