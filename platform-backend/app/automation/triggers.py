"""Trigger für den Dauerbetrieb (Auftrag §Phase 5): Zeitplan, Intervall, Event, Webhook.

Die Feuer-Entscheidung ist reine, testbare Logik (keine echte Uhr). Ein
`IdempotencyGuard` verhindert Doppelausführung bei identischer Auslösung —
wichtig für „genau einmal"-Semantik im 24/7-Betrieb.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class IntervalTrigger:
    every_seconds: float
    kind: Literal["interval"] = "interval"

    def should_fire(self, last_fired_at: float | None, now: float) -> bool:
        if last_fired_at is None:
            return True
        return (now - last_fired_at) >= self.every_seconds


@dataclass(frozen=True)
class DailyTrigger:
    """Täglich zu einer UTC-Uhrzeit. `now`/`last` als Unix-Sekunden."""

    hour: int
    minute: int = 0
    kind: Literal["daily"] = "daily"

    def should_fire(self, last_fired_at: float | None, now: float) -> bool:
        target = self.hour * 3600 + self.minute * 60
        scheduled_today = (now // 86_400) * 86_400 + target
        if now < scheduled_today:
            return False  # heutige Zielzeit noch nicht erreicht
        # Feuern, wenn seit dem heutigen geplanten Zeitpunkt noch nicht gefeuert.
        return last_fired_at is None or last_fired_at < scheduled_today


@dataclass(frozen=True)
class EventTrigger:
    event_name: str
    kind: Literal["event"] = "event"

    def matches(self, event: dict) -> bool:
        return event.get("name") == self.event_name


@dataclass(frozen=True)
class WebhookTrigger:
    path: str
    kind: Literal["webhook"] = "webhook"

    def matches(self, request_path: str) -> bool:
        return request_path.rstrip("/") == self.path.rstrip("/")


@dataclass
class IdempotencyGuard:
    """Merkt sich verarbeitete Keys → dieselbe Auslösung läuft nur einmal."""

    _seen: set = field(default_factory=set)

    def first_time(self, key: str) -> bool:
        if key in self._seen:
            return False
        self._seen.add(key)
        return True
