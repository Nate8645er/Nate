"""Fortschritt: echtes Level-Up durch echte Arbeit (Agent 2/3).

Jeder Mitarbeiter hat ein prozedurales Basis-Level (identity.py). ZUSÄTZLICH
sammelt er ECHTE Erfahrung, wenn er wirklich Aufgaben erledigt — gespeichert
pro Adresse in einer kleinen SQLite-DB. Aus verdienter Erfahrung werden
Bonus-Level: sichtbarer Fortschritt, der auf echter Arbeit beruht, nicht auf
Behauptungen.

  - 1 erledigte Aufgabe  = XP_PRO_AUFGABE Erfahrung
  - je BONUS_SCHWELLE XP  = +1 Bonus-Level (gedeckelt bei MAX_BONUS)
  - Gesamt-Level = min(99, Basis-Level + Bonus-Level)
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

XP_PRO_AUFGABE = 10
BONUS_SCHWELLE = 100        # XP je Bonus-Level
MAX_BONUS = 20             # maximal +20 Level durch Arbeit


def _bonus_from_xp(xp: int) -> int:
    return min(MAX_BONUS, xp // BONUS_SCHWELLE)


class Progression:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS fortschritt ("
            " address TEXT PRIMARY KEY, xp INTEGER, erledigt INTEGER)")
        self.conn.commit()
        self._lock = threading.Lock()

    def award(self, address: str, amount: int = XP_PRO_AUFGABE) -> dict:
        """Vergibt XP für erledigte Arbeit; meldet, ob ein Level-Up passierte."""
        with self._lock:
            row = self.conn.execute(
                "SELECT xp, erledigt FROM fortschritt WHERE address=?",
                (address,)).fetchone()
            alt_xp = row[0] if row else 0
            erledigt = (row[1] if row else 0) + 1
            neu_xp = alt_xp + amount
            self.conn.execute(
                "INSERT INTO fortschritt (address, xp, erledigt) VALUES (?,?,?) "
                "ON CONFLICT(address) DO UPDATE SET xp=?, erledigt=?",
                (address, neu_xp, erledigt, neu_xp, erledigt))
            self.conn.commit()
        alt_bonus, neu_bonus = _bonus_from_xp(alt_xp), _bonus_from_xp(neu_xp)
        return {"xp": neu_xp, "erledigt": erledigt, "bonus_level": neu_bonus,
                "level_up": neu_bonus > alt_bonus}

    def get(self, address: str) -> dict:
        row = self.conn.execute(
            "SELECT xp, erledigt FROM fortschritt WHERE address=?",
            (address,)).fetchone()
        xp = row[0] if row else 0
        return {"xp": xp, "erledigt": row[1] if row else 0,
                "bonus_level": _bonus_from_xp(xp)}

    def effective_level(self, base_level: int, address: str) -> int:
        return min(99, base_level + self.get(address)["bonus_level"])

    def top(self, limit: int = 10) -> list[dict]:
        rows = self.conn.execute(
            "SELECT address, xp, erledigt FROM fortschritt "
            "ORDER BY xp DESC LIMIT ?", (limit,)).fetchall()
        return [{"adresse": a, "xp": x, "erledigt": e,
                 "bonus_level": _bonus_from_xp(x)} for a, x, e in rows]

    def totals(self) -> dict:
        row = self.conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(xp),0), COALESCE(SUM(erledigt),0) "
            "FROM fortschritt").fetchone()
        return {"mitarbeiter_mit_fortschritt": row[0], "xp_gesamt": row[1],
                "aufgaben_gesamt": row[2]}
