"""Ergebnis-Cache + Tages-Budget für den Modell-Router (Auftrag §5.3/§5.4).

Rein und testbar. Der Ergebnis-Cache schlüsselt über Hash(Modell+Nachrichten+
Parameter); das Budget begrenzt Kosten pro Tenant (Schutz vor Kostenexplosion
durch Dauer-Agenten — Risiko #4 aus PHASE-1-PLAN.md).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field


def cache_key(model: str, messages: list[dict], params: dict | None = None) -> str:
    payload = json.dumps(
        {"model": model, "messages": messages, "params": params or {}},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class ResultCache:
    """TTL-Cache mit Höchstgröße (LRU-artig über Einfügereihenfolge)."""

    ttl_seconds: float = 3600.0
    max_entries: int = 1000
    _now: "callable" = field(default=time.monotonic, repr=False)
    _store: dict = field(default_factory=dict, repr=False)

    def get(self, key: str):
        item = self._store.get(key)
        if item is None:
            return None
        value, expires = item
        if self._now() >= expires:
            self._store.pop(key, None)
            return None
        return value

    def put(self, key: str, value) -> None:
        if len(self._store) >= self.max_entries and key not in self._store:
            # ältesten Eintrag entfernen (Insertion-Order)
            oldest = next(iter(self._store))
            self._store.pop(oldest, None)
        self._store[key] = (value, self._now() + self.ttl_seconds)

    def __len__(self) -> int:
        return len(self._store)


@dataclass
class TenantBudget:
    """Tages-Token-Budget je Tenant. Übersteigt eine Anfrage das Budget → Ablehnung."""

    daily_limit_tokens: int
    _used: dict = field(default_factory=dict, repr=False)
    _day: dict = field(default_factory=dict, repr=False)
    _today: "callable" = field(default=lambda: time.strftime("%Y-%m-%d", time.gmtime()), repr=False)

    def _roll(self, tenant: str) -> None:
        today = self._today()
        if self._day.get(tenant) != today:
            self._day[tenant] = today
            self._used[tenant] = 0

    def remaining(self, tenant: str) -> int:
        self._roll(tenant)
        return max(0, self.daily_limit_tokens - self._used.get(tenant, 0))

    def allow(self, tenant: str, tokens: int) -> bool:
        return tokens <= self.remaining(tenant)

    def charge(self, tenant: str, tokens: int) -> None:
        self._roll(tenant)
        self._used[tenant] = self._used.get(tenant, 0) + max(0, tokens)
