"""HyperScale-Orchestrator: verwaltet Milliarden ADRESSIERBARER Mitarbeiter,
führt aber nur so viele AKTIVE Agenten aus, wie die Hardware zulässt.

Kernideen:
  - Virtuell = Daten (prozedural berechnet, 0 Byte pro inaktivem Mitarbeiter)
  - Aktiv    = begrenzter asyncio-Worker-Pool (CPU-/RAM-abhängig)
  - Aufgaben laufen durch eine Queue; jeder Task materialisiert genau den
    einen Mitarbeiter, der ihn bearbeitet, und gibt ihn danach wieder frei.
  - Langzeitgedächtnis: SQLite, pro Mitarbeiter-Adresse.
"""

from __future__ import annotations

import asyncio
import itertools
import os
import sqlite3
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil

from . import brain
from .identity import ADDRESS_SPACE, address_for_task, materialize, team_members
from .plugins import PluginManager


def _parse_kwargs(rest: str, valid_keys: set[str] | None = None) -> dict[str, str]:
    """Parst 'key=value key2=value mit leerzeichen' — Wert läuft bis zum nächsten key=.

    `valid_keys` (die echten Parameternamen des Ziel-Plugins) verhindert, dass
    Freitext-Werte an einem eingebetteten 'wort=' zerhackt werden:
    z. B. 'prompt=setze debug=true in der config' bleibt EIN Wert, weil 'debug'
    kein gültiger Parameter ist. Ohne valid_keys splittet der Parser an jedem key=.
    """
    import re
    if not rest.strip():
        return {}
    keys = [m for m in re.finditer(r"(?:^|\s)([a-zA-Z_]\w*)=", rest)
            if valid_keys is None or m.group(1) in valid_keys]
    kwargs: dict[str, str] = {}
    for i, m in enumerate(keys):
        start = m.end()
        end = keys[i + 1].start() if i + 1 < len(keys) else len(rest)
        kwargs[m.group(1)] = rest[start:end].strip()
    return kwargs


def _plugin_param_names(plugin: Any) -> set[str] | None:
    """Echte Parameternamen der run()-Methode (ohne self/action).

    Nimmt run() **kwargs entgegen (z. B. das pc-Werkzeug), sind BELIEBIGE
    Schlüssel erlaubt -> None. Sonst würde der Parser bei solchen Werkzeugen
    ALLE Parameter verwerfen (Bug: 'program= fehlt' trotz program=…).
    """
    if plugin is None:
        return None
    import inspect
    try:
        params = inspect.signature(plugin.run).parameters
    except (TypeError, ValueError):
        return None
    named = {n for n, p in params.items()
             if n not in ("self", "action")
             and p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL)}
    if named:
        return named                   # explizite Parameter -> Freitext-Schutz aktiv
    has_var_kw = any(p.kind == p.VAR_KEYWORD for p in params.values())
    return None if has_var_kw else named   # nur **kwargs (z. B. pc) -> alle Schlüssel


def hardware_limit() -> int:
    """Wie viele Agenten kann diese Maschine gleichzeitig sinnvoll ausführen?"""
    cpu = os.cpu_count() or 4
    ram_gb = psutil.virtual_memory().available / 1_073_741_824
    return max(2, min(cpu * 8, int(ram_gb * 16), 128))


@dataclass
class Task:
    id: int
    description: str
    address: str
    status: str = "wartend"           # wartend | aktiv | fertig | fehler
    result: str = ""
    agent: str = ""
    team: str = ""
    boss: str = ""                    # Teamleiter, der die Aufgabe überwacht/delegiert
    kette: list = field(default_factory=list)      # JARVIS -> Chef -> Mitarbeiter
    mitwirkende: list = field(default_factory=list)  # Team-Kollegen, die mitwirken
    beitraege: list = field(default_factory=list)  # Team-Modus: einzelne Beiträge
    created: float = field(default_factory=time.time)
    finished: float = 0.0
    is_demo: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "beschreibung": self.description[:200],
                "adresse": self.address, "status": self.status,
                "agent": self.agent, "team": self.team, "chef": self.boss,
                "kette": self.kette, "mitwirkende": self.mitwirkende,
                "beitraege": self.beitraege,
                "ergebnis": self.result[:400], "demo": self.is_demo}


class Memory:
    """Langzeitgedächtnis pro Mitarbeiter-Adresse (SQLite)."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS memory ("
            " address TEXT, ts REAL, task TEXT, result TEXT)")
        self.conn.commit()
        self._lock = asyncio.Lock()

    async def remember(self, address: str, task: str, result: str) -> None:
        async with self._lock:
            self.conn.execute("INSERT INTO memory VALUES (?,?,?,?)",
                              (address, time.time(), task, result))
            self.conn.commit()

    def recall(self, address: str, limit: int = 5) -> list[tuple[str, str]]:
        rows = self.conn.execute(
            "SELECT task, result FROM memory WHERE address=? ORDER BY ts DESC LIMIT ?",
            (address, limit)).fetchall()
        return list(rows)

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]

    def recent(self, limit: int = 25) -> list[tuple[str, float, str, str]]:
        return list(self.conn.execute(
            "SELECT address, ts, task, result FROM memory ORDER BY ts DESC LIMIT ?",
            (limit,)).fetchall())


class Orchestrator:
    def __init__(self, data_dir: Path, max_active: int | None = None) -> None:
        self.max_active = max_active or hardware_limit()
        # Team-Modus (abschaltbar): mehrere Teammitglieder liefern eigene Beiträge,
        # der Chef führt sie zusammen. Im API-Modus mehrere Aufrufe pro Frage!
        self.team_mode = os.environ.get("JARVIS_TEAM_MODE") == "1"
        self.queue: asyncio.Queue[Task] = asyncio.Queue()
        self.active: dict[int, Task] = {}
        self.recent: deque[Task] = deque(maxlen=200)
        self.logs: deque[dict[str, Any]] = deque(maxlen=400)
        self.completed = 0
        self.failed = 0
        self.activated_agents = 0
        self._task_ids = itertools.count(1)
        self._workers: list[asyncio.Task] = []
        workspace = data_dir / "workspace"
        self.plugins = PluginManager(workspace)
        # Claude-Code-artige Tool-Suite + Claude-Code-Brücke registrieren
        from . import browser_auto, code_agent, desktop, tools
        tools.register_all(self.plugins, workspace)
        self.plugins.plugins["code"] = code_agent.CodeAgentPlugin(workspace)
        desktop.register(self.plugins, workspace)       # PC-Steuerung (eigener Schalter)
        browser_auto.register(self.plugins, workspace)  # Browser-Automatisierung
        from . import openrouter                          # Multi-Modell-Zugang (OpenRouter)
        openrouter.register(self.plugins, workspace)
        # Sicherheits-Modul + 30-Minuten-Monitor
        from .security import BodyguardSquad, SecurityMonitor, SecurityPlugin
        sec = SecurityPlugin()
        self.plugins.plugins["security"] = sec
        self.security = SecurityMonitor(sec, interval_s=1800)
        self.security.set_logger(self.log)
        # 24/7-Bodyguards: patrouillieren alle 5 Minuten
        self.bodyguards = BodyguardSquad(sec, interval_s=300)
        self.bodyguards.set_logger(self.log)
        # Skills-System (wie Claude Code / Claude.ai Skills)
        from .skills import SkillRegistry
        self.skills = SkillRegistry(data_dir / "skills")
        self.memory = Memory(data_dir / "memory.db")
        # Fortschritt: echtes Level-Up durch echte Arbeit
        from .progression import Progression
        self.progression = Progression(data_dir / "fortschritt.db")
        # Belegschaft-Betrieb: kontinuierliche Aktivierung des GESAMTEN Adressraums
        from .workforce import WorkforceEngine
        self.workforce = WorkforceEngine(waves=self.max_active)
        # 24/7-Autopilot: Mitarbeiter erfinden fortlaufend Geschäftsideen
        from .autopilot import Autopilot
        self.autopilot = Autopilot(data_dir)
        self.autopilot.set_logger(self.log)
        self.started = time.time()

    # -- Logging ------------------------------------------------------------
    def log(self, level: str, msg: str) -> None:
        self.logs.appendleft({"ts": time.strftime("%H:%M:%S"), "level": level, "msg": msg})

    # -- Aufgaben -----------------------------------------------------------
    def submit(self, description: str, address: str | None = None,
               is_demo: bool = False) -> Task:
        addr = address or self._route(description)
        task = Task(id=next(self._task_ids), description=description,
                    address=addr, is_demo=is_demo)
        self.queue.put_nowait(task)
        self.log("info", f"Aufgabe #{task.id} eingereiht -> Adresse {addr}")
        return task

    def _route(self, description: str) -> str:
        """Wählt eine Adresse. Tool-Aufgaben gehen an ein organisatorisch zuständiges Team.

        WICHTIG (Ehrlichkeit): Die Team-Zuordnung ist ORGANISATORISCH, keine
        Sicherheitsgrenze. Die einzige echte Schranke für OS-weitreichende
        Werkzeuge ist das Env-Gate (JARVIS_ALLOW_DANGEROUS / JARVIS_ALLOW_PC) in
        PluginManager.run — dieses kann durch Routing NICHT umgangen werden.
        """
        routed = description
        if not routed.startswith(("!plugin", "!skill")):
            from .commands import interpret
            mapped = interpret(routed)
            if mapped:
                routed = mapped
        if routed.startswith("!plugin"):
            parts = routed.split()
            if len(parts) >= 2:
                plugin = self.plugins.plugins.get(parts[1])
                if plugin is not None and plugin.allowed_teams:
                    return address_for_task(description, team_hint=plugin.allowed_teams[0])
        return address_for_task(description)

    async def _run_task(self, task: Task) -> None:
        try:
            employee = materialize(task.address)
        except ValueError as e:
            # Ungültige Adresse darf niemals den Worker töten — sauber als Fehler beenden.
            task.status = "fehler"
            task.result = f"Ungültige Mitarbeiter-Adresse {task.address!r}: {e}"
            task.finished = time.time()
            self.failed += 1
            self.recent.appendleft(task)
            self.log("warn", f"#{task.id} abgelehnt: ungültige Adresse {task.address!r}")
            return
        task.agent = employee.display
        task.team = employee.team
        # Team-Chef überwacht: der Teamleiter delegiert an das Teammitglied.
        boss = materialize(employee.boss_address)
        task.boss = boss.display
        # Sichtbare Bearbeitungskette: JARVIS -> Teamleiter -> Mitarbeiter,
        # plus mitwirkende Team-Kollegen (echte Organisationsstruktur).
        # Team-Kollegen EINMAL berechnen und für Anzeige + XP wiederverwenden
        # (früher doppelt materialisiert — Agent 5: unnötige Arbeit entfernt).
        mates = team_members(employee.address, n=3)
        kette = [{"rolle": "JARVIS", "name": "Koordinator", "info": "nimmt an & leitet weiter"},
                 {"rolle": "Teamleiter", "name": boss.name, "team": boss.team,
                  "info": "verteilt im Team"}]
        if not employee.is_team_boss:
            kette.append({"rolle": "Mitarbeiter", "name": employee.name,
                          "team": employee.team, "info": "führt aus"})
        task.kette = kette
        task.mitwirkende = [{"name": m.name, "rolle": m.role} for m in mates]
        task.status = "aktiv"
        self.active[task.id] = task
        self.activated_agents += 1
        if employee.is_team_boss:
            self.log("info", f"#{task.id} aktiv: Teamleiter {employee.name} bearbeitet selbst")
        else:
            self.log("info", f"#{task.id}: JARVIS → Teamleiter {boss.name} → {employee.name} "
                             f"(+{len(task.mitwirkende)} Kollegen)")
        try:
            # Freie Sätze zuerst auf ein echtes Kommando prüfen ("öffne YouTube" -> Aktion)
            command = task.description
            if not command.startswith(("!plugin", "!skill")):
                from .commands import interpret
                mapped = interpret(command)
                if mapped:
                    command = mapped

            if command.startswith("!plugin"):
                # Syntax: !plugin <name> <aktion> [key=value ...]
                # Werte dürfen Leerzeichen enthalten (bis zum nächsten bekannten key=).
                parts = command.split(maxsplit=3)
                if len(parts) < 3:
                    raise ValueError("Syntax: !plugin <name> <aktion> [key=value ...]")
                name, action = parts[1], parts[2]
                valid = _plugin_param_names(self.plugins.plugins.get(name))
                kwargs = _parse_kwargs(parts[3] if len(parts) > 3 else "", valid)
                result = await asyncio.to_thread(
                    self.plugins.run, employee.team, name, action, **kwargs)
                task.result = str(result)
            elif command.startswith("!skill"):
                # Syntax: !skill <name> <aufgabentext...>
                parts = command.split(maxsplit=2)
                if len(parts) < 2:
                    raise ValueError("Syntax: !skill <name> <aufgabentext...>")
                prompt = self.skills.apply(parts[1], parts[2] if len(parts) > 2 else "")
                task.result = await asyncio.to_thread(brain.answer, employee, prompt)
            elif self.team_mode:
                task.result = await self._team_answer(employee, boss, task)
            else:
                task.result = await asyncio.to_thread(brain.answer, employee, task.description)
            task.status = "fertig"
            self.completed += 1
            await self.memory.remember(task.address, task.description, task.result)
            # Echtes Level-Up: der Mitarbeiter verdient volle Erfahrung für echte Arbeit.
            fort = self.progression.award(task.address)
            if fort["level_up"]:
                self.log("info", f"⬆ {employee.name} steigt auf — Bonus-Level "
                                 f"{fort['bonus_level']} ({fort['erledigt']} Aufgaben)")
            # Der Teamleiter bekommt Führungs-XP fürs Delegieren/Überwachen.
            if not employee.is_team_boss:
                bf = self.progression.award(employee.boss_address, amount=3)
                if bf["level_up"]:
                    self.log("info", f"⬆ Teamleiter {boss.name} steigt durch Führung auf — "
                                     f"Bonus-Level {bf['bonus_level']}")
            # Mitwirkende Team-Kollegen erhalten etwas Unterstützungs-XP (alle wirken mit).
            # Wiederverwendung der oben EINMAL berechneten Liste (kein Neu-Materialisieren).
            for m in mates:
                self.progression.award(m.address, amount=1)
        except Exception as e:
            task.status = "fehler"
            task.result = f"{type(e).__name__}: {e}"
            self.failed += 1
            self.log("warn", f"#{task.id} fehlgeschlagen: {task.result[:120]}")
        finally:
            task.finished = time.time()
            self.active.pop(task.id, None)
            self.recent.appendleft(task)

    async def _team_answer(self, employee: Any, boss: Any, task: Task) -> str:
        """Team-Modus: mehrere Mitglieder liefern EIGENE echte Beiträge, der Chef
        führt sie zu einer Antwort zusammen. Im API-Modus mehrere Aufrufe!"""
        members = [employee] + team_members(employee.address, n=2)  # Bearbeiter + 2 Kollegen
        # Jedes Mitglied beantwortet die Frage eigenständig (echte Aufrufe, parallel).
        contribs = await asyncio.gather(
            *[asyncio.to_thread(brain.answer, m, task.description) for m in members])
        task.beitraege = [{"name": m.name, "rolle": m.role, "beitrag": c}
                          for m, c in zip(members, contribs)]
        self.log("info", f"#{task.id} Team-Modus: {len(members)} Beiträge, "
                         f"{boss.name} führt zusammen ({len(members) + 1} Modell-Aufrufe)")
        # Der Chef führt die Beiträge zu einer konsolidierten Antwort zusammen.
        zusammenfassung = (
            f"Als Teamleiter führst du die Beiträge deines Teams zu EINER besten, "
            f"widerspruchsfreien Antwort auf die Frage zusammen. Frage: "
            f"„{task.description}\"\n\n" +
            "\n".join(f"Beitrag {i + 1} ({b['name']}): {b['beitrag']}"
                      for i, b in enumerate(task.beitraege)) +
            "\n\nGib nur die konsolidierte Endantwort auf Deutsch, ohne die Beiträge "
            "zu wiederholen. Erfinde nichts dazu.")
        final = await asyncio.to_thread(brain.answer, boss, zusammenfassung)
        return final

    async def _worker(self) -> None:
        while True:
            task = await self.queue.get()
            try:
                await self._run_task(task)
            except Exception as e:  # Sicherheitsnetz: kein Fehler darf den Worker-Slot töten
                task.status = "fehler"
                task.result = f"{type(e).__name__}: {e}"
                task.finished = time.time()
                self.failed += 1
                self.active.pop(task.id, None)
                self.recent.appendleft(task)
                self.log("warn", f"#{task.id} Worker-Fehler abgefangen: {task.result[:120]}")
            finally:
                self.queue.task_done()

    async def start(self) -> None:
        if self._workers:
            return
        self._workers = [asyncio.create_task(self._worker())
                         for _ in range(self.max_active)]
        self.log("info", f"Orchestrator gestartet: {self.max_active} parallele "
                         f"Agenten-Slots (Hardware-Limit), Modellmodus: {brain.mode()}")

    async def stop(self) -> None:
        self.workforce.stop()
        self.autopilot.stop()
        self.security.stop()
        self.bodyguards.stop()
        for w in self._workers:
            w.cancel()
        self._workers.clear()

    def find_task(self, task_id: int) -> Task | None:
        if task_id in self.active:
            return self.active[task_id]
        for t in self.recent:
            if t.id == task_id:
                return t
        return None

    def answer_now(self, description: str) -> str:
        """Verarbeitet EINEN Befehl SYNCHRON und gibt die Antwort als Klartext.

        Für die Kurzbefehle-/Siri-Schnittstelle: dieselbe Logik wie eine Aufgabe
        (Befehl erkennen → Werkzeug ODER Gehirn), aber sofort und ohne Queue,
        damit Siri die Antwort direkt vorlesen kann.
        """
        description = (description or "").strip()
        if not description:
            return "Kein Befehl übergeben."
        try:
            employee = materialize(self._route(description))
        except ValueError:
            employee = materialize("0/0/0")
        command = description
        if not command.startswith(("!plugin", "!skill")):
            from .commands import interpret
            mapped = interpret(command)
            if mapped:
                command = mapped
        try:
            if command.startswith("!plugin"):
                parts = command.split(maxsplit=3)
                if len(parts) < 3:
                    return "Syntax: !plugin <name> <aktion> [key=value ...]"
                name, action = parts[1], parts[2]
                valid = _plugin_param_names(self.plugins.plugins.get(name))
                kwargs = _parse_kwargs(parts[3] if len(parts) > 3 else "", valid)
                result = self.plugins.run(employee.team, name, action, **kwargs)
                # Erfolgreiche echte Arbeit wird belohnt (wie bei Aufgaben).
                self.progression.award(employee.address)
                return str(result)
            if command.startswith("!skill"):
                parts = command.split(maxsplit=2)
                if len(parts) < 2:
                    return "Syntax: !skill <name> <aufgabentext...>"
                prompt = self.skills.apply(parts[1], parts[2] if len(parts) > 2 else "")
                return brain.answer(employee, prompt)
            return brain.answer(employee, description)
        except PermissionError as e:
            return f"[gesperrt] {e}"
        except Exception as e:  # nie den Aufrufer (Siri) mit 500 abwürgen
            return f"[Fehler] {type(e).__name__}: {e}"

    # -- Zustand für das Dashboard -------------------------------------------
    def finanzen(self) -> dict[str, Any]:
        """Ziel-Tracker: Ziel vs. real erfasste Einnahmen (keine Simulation)."""
        # Ziel robust parsen: Schweizer Tausenderformat (1'000'000), Kommas und
        # ungültige/0-Werte dürfen /api/state nie mit 500 abstürzen lassen.
        raw = str(os.environ.get("JARVIS_ZIEL_CHF", "1000000000"))
        try:
            ziel = float(raw.replace("'", "").replace(",", "").replace(" ", "").replace("_", ""))
        except (ValueError, TypeError):
            ziel = 1_000_000_000.0
        if ziel <= 0:
            ziel = 1_000_000_000.0
        try:
            s = self.plugins.plugins["finanzen"].run("summe")
        except Exception:
            s = {"einnahmen": 0.0, "ausgaben": 0.0, "saldo": 0.0, "eintraege": 0}
        return {"ziel_chf": ziel, "einnahmen_chf": s["einnahmen"],
                "ausgaben_chf": s["ausgaben"], "saldo_chf": s["saldo"],
                "eintraege": s["eintraege"],
                "fortschritt_prozent": round(s["einnahmen"] / ziel * 100, 8)}

    def state(self) -> dict[str, Any]:
        vm = psutil.virtual_memory()
        return {
            "finanzen": self.finanzen(),
            "adressraum_pro_ebene": ADDRESS_SPACE,
            "adressierbare_mitarbeiter": "100 Mrd. pro Ebene, rekursiv (prozedural, 0 Byte/inaktiv)",
            "aktivierte_agenten_gesamt": self.activated_agents,
            "aktive_agenten": len(self.active),
            "wartende_aufgaben": self.queue.qsize(),
            "max_parallel": self.max_active,
            "fertig": self.completed,
            "fehler": self.failed,
            "gedaechtnis_eintraege": self.memory.count(),
            "cpu_prozent": psutil.cpu_percent(interval=None),
            "ram_prozent": vm.percent,
            "ram_frei_mb": vm.available // 1_048_576,
            "modell_modus": brain.mode(),
            "modell": brain.active_model(),   # tatsächlich aktives Modell (inkl. Fallback)
            "laufzeit_s": int(time.time() - self.started),
            "aktive": [t.as_dict() for t in list(self.active.values())[:50]],
            "letzte_aufgaben": [t.as_dict() for t in list(self.recent)[:30]],
            "logs": list(self.logs)[:60],
            "plugins": self.plugins.status(),
            "skills": [{"name": s.name, "description": s.description} for s in self.skills.all()],
            "team_modus": self.team_mode,
            "fortschritt": self.progression.totals(),
            "belegschaft": self.workforce.stats(),
            "autopilot": self.autopilot.stats(),
            "sicherheit": self.security.stats(),
            "bodyguards": self.bodyguards.stats(),
        }
