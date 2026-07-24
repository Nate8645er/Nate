"""Kontingente pro Tenant (Auftrag §6) — Schutz vor Kostenexplosion.

Verallgemeinert das Tages-Token-Budget aus Phase 2 auf beliebige Ressourcen
(z. B. tokens, missions, storage_mb). Grenzen gelten pro Tenant und Tag; eine
Anfrage über dem Rest wird abgelehnt, bevor Kosten entstehen.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field


class QuotaExceeded(Exception):
    def __init__(self, tenant: str, resource: str, requested: int, remaining: int) -> None:
        super().__init__(
            f"Kontingent überschritten: {tenant}/{resource} "
            f"(angefragt {requested}, frei {remaining})"
        )
        self.tenant = tenant
        self.resource = resource


@dataclass
class QuotaManager:
    #: Ressource -> Tageslimit.
    limits: dict[str, int]
    _today: Callable[[], str] = field(
        default=lambda: time.strftime("%Y-%m-%d", time.gmtime()), repr=False
    )
    _used: dict[tuple[str, str], int] = field(default_factory=dict, repr=False)
    _day: dict[str, str] = field(default_factory=dict, repr=False)

    def _roll(self, tenant: str) -> None:
        today = self._today()
        if self._day.get(tenant) != today:
            self._day[tenant] = today
            for key in [k for k in self._used if k[0] == tenant]:
                self._used.pop(key, None)

    def remaining(self, tenant: str, resource: str) -> int:
        if resource not in self.limits:
            raise KeyError(f"unbekannte Ressource: {resource}")
        self._roll(tenant)
        return max(0, self.limits[resource] - self._used.get((tenant, resource), 0))

    def allow(self, tenant: str, resource: str, amount: int = 1) -> bool:
        return amount <= self.remaining(tenant, resource)

    def consume(self, tenant: str, resource: str, amount: int = 1) -> None:
        """Verbraucht Kontingent oder wirft QuotaExceeded (atomar geprüft)."""
        rem = self.remaining(tenant, resource)
        if amount > rem:
            raise QuotaExceeded(tenant, resource, amount, rem)
        self._used[(tenant, resource)] = self._used.get((tenant, resource), 0) + amount
