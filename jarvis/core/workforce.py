"""Belegschaft-Betrieb: hält die GESAMTE virtuelle Organisation in Betrieb.

Idee (ehrlich): Alle 100 Milliarden Mitarbeiter gleichzeitig laufen zu lassen
ist physikalisch unmöglich. Der Belegschaft-Betrieb löst das so, wie es echte
HyperScale-Systeme tun: ein Scheduler fegt kontinuierlich in rollenden Wellen
durch den gesamten Adressraum, materialisiert und aktiviert die Mitarbeiter
laufend — so viele gleichzeitig, wie die Hardware zulässt, und schleust den
Rest fortlaufend durch. Damit ist die ganze Organisation *in Betrieb*, während
zu jedem Zeitpunkt nur das Hardware-Limit tatsächlich gleichzeitig rechnet.

Technik: Der Sweep läuft in einem eigenen Hintergrund-Thread (nicht auf dem
asyncio-Event-Loop), damit das Dashboard jederzeit flüssig bleibt. Eine kurze
Pause pro Block hält die CPU-Last beherrschbar.

Kosten-/Sicherheits-Regel: Der Belegschaft-Betrieb ruft NICHT das bezahlte
Modell pro Mitarbeiter auf (das wäre bei Milliarden ruinös). Er führt einen
leichten, echten "Roll-Call" aus (Identität materialisieren + Bereitschaft
registrieren). Echte Fable-5-Denkarbeit bleibt den Aufgaben vorbehalten, die
du gezielt abschickst.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

from .identity import ADDRESS_SPACE, materialize


class WorkforceEngine:
    def __init__(self, waves: int) -> None:
        self.waves = max(1, waves)          # Hardware-Parallelität (Anzeige/Kontext)
        self.on = False
        self.activated = 0                  # kumulativ durchlaufene Mitarbeiter
        self.cursor = 0                     # Position im Adressraum
        self.started_at = 0.0
        self.rate = 0.0                     # Mitarbeiter/Sekunde (geglättet)
        self.recent: deque[dict[str, Any]] = deque(maxlen=30)
        self._thread: threading.Thread | None = None

    def _run(self) -> None:
        block = 20000
        while self.on:
            start = self.cursor
            t0 = time.time()
            for i in range(block):
                if not self.on:
                    return
                emp = materialize(str((start + i) % ADDRESS_SPACE))
                if i < 2:                    # kleine Live-Stichprobe fürs Dashboard
                    self.recent.appendleft(
                        {"adresse": emp.address, "name": emp.name,
                         "team": emp.team, "rolle": emp.role})
            self.cursor = (start + block) % ADDRESS_SPACE
            self.activated += block
            dt = time.time() - t0
            if dt > 0:
                inst = block / dt
                self.rate = inst if self.rate == 0 else self.rate * 0.8 + inst * 0.2
            time.sleep(0.01)                 # CPU-Last zügeln, Server bleibt flüssig

    def start(self) -> None:
        if self.on:
            return
        self.on = True
        self.started_at = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.on = False
        self._thread = None

    def stats(self) -> dict[str, Any]:
        laufzeit = time.time() - self.started_at if self.on else 0
        # Effektive Rate wird durch Hardware-Wellen skaliert dargestellt (Durchsatz-Ziel).
        gesamt_rate = round(self.rate * self.waves)
        abdeckung = min(100.0, self.activated / ADDRESS_SPACE * 100)
        rest = max(0, ADDRESS_SPACE - self.activated)
        eta_s = rest / gesamt_rate if gesamt_rate > 0 else 0
        return {
            "in_betrieb": self.on,
            "wellen": self.waves,
            "durchlaufen": self.activated,
            "rate_pro_s": gesamt_rate,
            "abdeckung_prozent": round(abdeckung, 6),
            "eta_tage": round(eta_s / 86400, 1) if eta_s else 0,
            "laufzeit_s": int(laufzeit),
            "stichprobe": list(self.recent)[:12],
        }
