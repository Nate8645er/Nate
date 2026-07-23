"""Genehmigungs-Queue (Auftrag §6).

Riskante Werkzeugaufrufe landen hier und werden erst nach menschlicher Freigabe
ausgeführt. Mandanten-scoped: ein Tenant sieht/entscheidet nur seine eigenen
Anfragen. Zustand ist serialisierbar (DB-fähig).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ApprovalRequest:
    id: str
    tenant: str
    run_id: str
    tool: str
    args: dict
    reason: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: str | None = None

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["status"] = self.status.value
        return d


class ApprovalQueue:
    """In-Memory-Queue (Interface identisch zu einer späteren DB-Implementierung)."""

    def __init__(self) -> None:
        self._by_id: dict[str, ApprovalRequest] = {}
        self._counter = 0

    def submit(self, tenant: str, run_id: str, tool: str, args: dict, reason: str = "") -> ApprovalRequest:
        if not tenant:
            raise ValueError("Freigabe verlangt einen tenant")
        self._counter += 1
        req = ApprovalRequest(id=f"apr-{self._counter}", tenant=tenant, run_id=run_id,
                              tool=tool, args=args, reason=reason)
        self._by_id[req.id] = req
        return req

    def pending(self, tenant: str) -> list[ApprovalRequest]:
        return [r for r in self._by_id.values()
                if r.tenant == tenant and r.status is ApprovalStatus.PENDING]

    def get(self, tenant: str, request_id: str) -> ApprovalRequest | None:
        req = self._by_id.get(request_id)
        # Isolation: fremder Tenant sieht die Anfrage nicht.
        return req if req and req.tenant == tenant else None

    def approve(self, tenant: str, request_id: str, by: str) -> ApprovalRequest:
        return self._decide(tenant, request_id, ApprovalStatus.APPROVED, by)

    def reject(self, tenant: str, request_id: str, by: str) -> ApprovalRequest:
        return self._decide(tenant, request_id, ApprovalStatus.REJECTED, by)

    def _decide(self, tenant: str, request_id: str, status: ApprovalStatus, by: str) -> ApprovalRequest:
        req = self.get(tenant, request_id)
        if req is None:
            raise KeyError(f"Freigabe nicht gefunden (oder fremder Tenant): {request_id}")
        if req.status is not ApprovalStatus.PENDING:
            raise ValueError(f"Freigabe bereits entschieden: {req.status.value}")
        req.status = status
        req.decided_by = by
        return req
