"""Audit-Log (Auftrag §6) — wer hat wann was getan.

Append-only: Einträge werden nur angehängt, nie geändert oder gelöscht. Jeder
Eintrag ist mandantengebunden. `InMemoryAuditLog` für Tests/kleine Fälle;
`SqlAuditLog` schreibt in die DB (append-only per Interface, zusätzlich per
DB-Rechten absicherbar).
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from sqlalchemy import JSON, BigInteger, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .tenancy import Base


@dataclass(frozen=True)
class AuditEvent:
    id: str
    tenant: str
    actor: str          # Principal.subject
    action: str         # z. B. "agent.run", "approval.approve"
    resource: str       # betroffene Ressource/ID
    ts: int             # Unix-Sekunden
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@runtime_checkable
class AuditLog(Protocol):
    def record(self, tenant: str, actor: str, action: str, resource: str, detail: dict | None = None) -> AuditEvent: ...
    def list(self, tenant: str, limit: int = 100) -> list[AuditEvent]: ...


class InMemoryAuditLog:
    def __init__(self, now: Callable[[], int] | None = None) -> None:
        self._events: list[AuditEvent] = []
        self._now = now or (lambda: int(time.time()))

    def record(self, tenant: str, actor: str, action: str, resource: str, detail: dict | None = None) -> AuditEvent:
        if not tenant:
            raise ValueError("Audit verlangt einen tenant")
        ev = AuditEvent(str(uuid.uuid4()), tenant, actor, action, resource, self._now(), detail or {})
        self._events.append(ev)  # nur anhängen
        return ev

    def list(self, tenant: str, limit: int = 100) -> list[AuditEvent]:
        return [e for e in reversed(self._events) if e.tenant == tenant][:limit]


class AuditRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    actor: Mapped[str] = mapped_column(String(128), default="")
    action: Mapped[str] = mapped_column(String(128), index=True)
    resource: Mapped[str] = mapped_column(String(256), default="")
    ts: Mapped[int] = mapped_column(BigInteger)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


class SqlAuditLog:
    """Append-only Audit in der DB. Kein update/delete im Interface."""

    def __init__(self, session: Session, now: Callable[[], int] | None = None) -> None:
        self._session = session
        self._now = now or (lambda: int(time.time()))

    def record(self, tenant: str, actor: str, action: str, resource: str, detail: dict | None = None) -> AuditEvent:
        if not tenant:
            raise ValueError("Audit verlangt einen tenant")
        ev = AuditEvent(str(uuid.uuid4()), tenant, actor, action, resource, self._now(), detail or {})
        self._session.add(AuditRow(id=ev.id, tenant_id=tenant, actor=actor, action=action,
                                   resource=resource, ts=ev.ts, detail=ev.detail))
        self._session.flush()
        return ev

    def list(self, tenant: str, limit: int = 100) -> list[AuditEvent]:
        stmt = (select(AuditRow).where(AuditRow.tenant_id == tenant)
                .order_by(AuditRow.ts.desc()).limit(limit))
        return [AuditEvent(r.id, r.tenant_id, r.actor, r.action, r.resource, r.ts, r.detail)
                for r in self._session.scalars(stmt)]
