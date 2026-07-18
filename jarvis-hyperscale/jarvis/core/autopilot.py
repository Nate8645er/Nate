"""24/7-Autopilot: Mitarbeiter erfinden fortlaufend eigene Geschäftsideen.

Ehrlich: Der Autopilot erzeugt echte ARBEIT (Ideen, Konzepte, Entwürfe) —
er verdient KEIN Geld von allein. Aus einer Idee echtes Geld zu machen,
verlangt einen Menschen, der sie umsetzt (Shop, Zahlung, Verkauf). Der
Autopilot liefert dir die Vorarbeit; das Finanz-Panel zeigt weiter nur real
erfasste Einnahmen.

Kostenhinweis: Läuft das Gehirn im API-Modus, kostet jede erzeugte Idee
einen echten Fable-5-Aufruf. Deshalb ist das Intervall bewusst gemächlich
(Standard: alle 3 Minuten eine Idee) und im Dashboard einstellbar/stoppbar.
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

from . import brain
from .identity import address_for_task, materialize

IDEA_PROMPT = (
    "Erfinde EINE konkrete, umsetzbare Online-Business-Idee für eine Einzelperson "
    "mit kleinem Budget. Antworte kurz und strukturiert auf Deutsch mit genau diesen "
    "Feldern:\n"
    "TITEL: <kurzer Name>\n"
    "IDEE: <1-2 Sätze>\n"
    "ZIELGRUPPE: <wer>\n"
    "ERSTER SCHRITT: <was der Mensch heute konkret tun müsste>\n"
    "Erfinde keine Umsätze und behaupte keinen garantierten Gewinn."
)


class Autopilot:
    def __init__(self, data_dir: Path, interval_s: int = 180) -> None:
        self.interval = max(20, interval_s)
        self.on = False
        self.store = data_dir / "ideen.jsonl"
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.count_total = self._count_file()
        self.recent: deque[dict[str, Any]] = deque(maxlen=30)
        self._thread: threading.Thread | None = None
        self._gen = 0     # Generations-Token: verhindert doppelte Idee-Threads bei stop()+start()
        self._log = None  # optionaler Logger-Callback
        # In-Memory-Cache für heutige Ideen (kein wiederholtes Datei-Lesen im Betrieb)
        self._today_date = time.strftime("%Y-%m-%d")
        self._today: list[dict[str, Any]] = self._load_today()

    def _count_file(self) -> int:
        if not self.store.exists():
            return 0
        return sum(1 for _ in self.store.open(encoding="utf-8"))

    def _load_today(self) -> list[dict[str, Any]]:
        """Liest die heutigen Ideen EINMAL beim Start aus der Datei."""
        heute = time.strftime("%Y-%m-%d")
        out: list[dict[str, Any]] = []
        if self.store.exists():
            for line in self.store.open(encoding="utf-8"):
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("zeit", "").startswith(heute):
                    out.append(e)
        return out

    def _roll_day(self) -> None:
        """Bei Tageswechsel den heutigen Cache zurücksetzen."""
        heute = time.strftime("%Y-%m-%d")
        if heute != self._today_date:
            self._today_date = heute
            self._today = []

    def set_logger(self, fn: Any) -> None:
        self._log = fn

    def _run(self, gen: int) -> None:
        while self.on and gen == self._gen:
            addr = address_for_task("business idee", team_hint="Business")
            emp = materialize(addr)
            try:
                # Ideenfindung ist kreative Mitarbeiter-Arbeit -> Worker (Sol Ultra).
                text = brain.answer(emp, IDEA_PROMPT, role="worker")
            except Exception as e:  # nie abstürzen
                text = f"[Fehler bei Ideengenerierung: {type(e).__name__}]"
            entry = {"ts": time.time(),
                     "zeit": time.strftime("%Y-%m-%d %H:%M"),
                     "von": emp.display, "team": emp.team, "text": text}
            with self.store.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.count_total += 1
            self.recent.appendleft(entry)
            self._roll_day()
            self._today.append(entry)
            if self._log:
                self._log("info", f"Autopilot: neue Idee von {emp.display}")
            # Intervall in kleinen Schritten, damit Stop schnell greift
            for _ in range(self.interval):
                if not self.on or gen != self._gen:
                    return
                time.sleep(1)

    def start(self) -> None:
        if self.on:
            return
        self.on = True
        self._gen += 1                       # neue Generation; ein evtl. alter Thread endet
        gen = self._gen
        self._thread = threading.Thread(target=self._run, args=(gen,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.on = False
        self._gen += 1                       # laufenden Thread sicher beenden
        self._thread = None

    def today(self) -> list[dict[str, Any]]:
        """Heutige Ideen aus dem In-Memory-Cache (kein Datei-Read im Betrieb)."""
        self._roll_day()
        return list(self._today)

    def stats(self) -> dict[str, Any]:
        return {
            "laeuft": self.on,
            "intervall_s": self.interval,
            "ideen_gesamt": self.count_total,
            "ideen_heute": len(self.today()),
            "modus": brain.mode(),
            "letzte": [
                {"zeit": e["zeit"], "von": e["von"], "team": e.get("team", ""),
                 "text": e["text"][:600]}
                for e in list(self.recent)[:10]
            ],
        }
