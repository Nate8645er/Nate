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
from .identity import ADDRESS_SPACE, address_for_task, materialize
from .plugins import PluginManager


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
    created: float = field(default_factory=time.time)
    finished: float = 0.0
    is_demo: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "beschreibung": self.description[:200],
                "adresse": self.address, "status": self.status,
                "agent": self.agent, "team": self.team,
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


class Orchestrator:
    def __init__(self, data_dir: Path, max_active: int | None = None) -> None:
        self.max_active = max_active or hardware_limit()
        self.queue: asyncio.Queue[Task] = asyncio.Queue()
        self.active: dict[int, Task] = {}
        self.recent: deque[Task] = deque(maxlen=200)
        self.logs: deque[dict[str, Any]] = deque(maxlen=400)
        self.completed = 0
        self.failed = 0
        self.activated_agents = 0
        self._task_ids = itertools.count(1)
        self._workers: list[asyncio.Task] = []
        self.plugins = PluginManager(data_dir / "workspace")
        self.memory = Memory(data_dir / "memory.db")
        self.started = time.time()

    # -- Logging ------------------------------------------------------------
    def log(self, level: str, msg: str) -> None:
        self.logs.appendleft({"ts": time.strftime("%H:%M:%S"), "level": level, "msg": msg})

    # -- Aufgaben -----------------------------------------------------------
    def submit(self, description: str, address: str | None = None,
               is_demo: bool = False) -> Task:
        addr = address or address_for_task(description)
        task = Task(id=next(self._task_ids), description=description,
                    address=addr, is_demo=is_demo)
        self.queue.put_nowait(task)
        self.log("info", f"Aufgabe #{task.id} eingereiht -> Adresse {addr}")
        return task

    async def _run_task(self, task: Task) -> None:
        employee = materialize(task.address)
        task.agent = employee.display
        task.team = employee.team
        task.status = "aktiv"
        self.active[task.id] = task
        self.activated_agents += 1
        self.log("info", f"#{task.id} aktiv: {employee.display}")
        try:
            if task.description.startswith("!plugin"):
                # Syntax: !plugin <name> <aktion> [key=value ...]
                parts = task.description.split()
                kwargs = dict(p.split("=", 1) for p in parts[3:] if "=" in p)
                result = self.plugins.run(employee.team, parts[1], parts[2], **kwargs)
                task.result = str(result)
            else:
                task.result = await asyncio.to_thread(brain.answer, employee, task.description)
            task.status = "fertig"
            self.completed += 1
            await self.memory.remember(task.address, task.description, task.result)
        except Exception as e:
            task.status = "fehler"
            task.result = f"{type(e).__name__}: {e}"
            self.failed += 1
            self.log("warn", f"#{task.id} fehlgeschlagen: {task.result[:120]}")
        finally:
            task.finished = time.time()
            self.active.pop(task.id, None)
            self.recent.appendleft(task)

    async def _worker(self) -> None:
        while True:
            task = await self.queue.get()
            await self._run_task(task)
            self.queue.task_done()

    async def start(self) -> None:
        if self._workers:
            return
        self._workers = [asyncio.create_task(self._worker())
                         for _ in range(self.max_active)]
        self.log("info", f"Orchestrator gestartet: {self.max_active} parallele "
                         f"Agenten-Slots (Hardware-Limit), Modellmodus: {brain.mode()}")

    async def stop(self) -> None:
        for w in self._workers:
            w.cancel()
        self._workers.clear()

    # -- Zustand für das Dashboard -------------------------------------------
    def state(self) -> dict[str, Any]:
        vm = psutil.virtual_memory()
        return {
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
            "modell": brain.DEFAULT_MODEL,
            "laufzeit_s": int(time.time() - self.started),
            "aktive": [t.as_dict() for t in list(self.active.values())[:50]],
            "letzte_aufgaben": [t.as_dict() for t in list(self.recent)[:30]],
            "logs": list(self.logs)[:60],
            "plugins": self.plugins.status(),
        }
