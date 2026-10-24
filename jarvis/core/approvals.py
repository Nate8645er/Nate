"""User approval gate for system actions.

JARVIS never touches the machine without permission: every skill invocation
declares a risk level, and anything at or above the configured threshold is
routed here. The request is published on the event bus, shown in the UI
(and spoken aloud), and blocks until the user approves or denies it.

Risk levels:
    0 READ    — read-only (list files, read calendar)
    1 WRITE   — creates/modifies user data (write file, create document)
    2 SYSTEM  — controls the machine (launch apps, shell, browser, docker)
    3 CRITICAL— destructive or outward-facing (delete, send email, payments)
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from jarvis.core.events import EventBus


class Risk(IntEnum):
    READ = 0
    WRITE = 1
    SYSTEM = 2
    CRITICAL = 3


@dataclass
class ApprovalRequest:
    action: str
    detail: str
    risk: Risk
    requested_by: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    future: asyncio.Future[bool] = field(default_factory=lambda: asyncio.get_event_loop().create_future())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "detail": self.detail,
            "risk": int(self.risk),
            "requested_by": self.requested_by,
            "created_at": self.created_at,
        }


class ApprovalManager:
    """Blocks risky actions until the user says yes."""

    def __init__(self, bus: EventBus, threshold: int = 1, timeout: float = 120.0) -> None:
        self.bus = bus
        self.threshold = threshold
        self.timeout = timeout
        self.pending: dict[str, ApprovalRequest] = {}
        # Session grants: "action" -> True lets repeated identical actions through.
        self._session_grants: set[str] = set()

    def grant_for_session(self, action: str) -> None:
        self._session_grants.add(action)

    async def request(
        self, action: str, detail: str, risk: Risk, requested_by: str = "system"
    ) -> bool:
        """Return True if the action may proceed."""
        if int(risk) < self.threshold or action in self._session_grants:
            return True

        req = ApprovalRequest(action=action, detail=detail, risk=risk, requested_by=requested_by)
        self.pending[req.id] = req
        await self.bus.publish("approval.requested", req.to_dict(), source=requested_by)
        try:
            return await asyncio.wait_for(req.future, self.timeout)
        except asyncio.TimeoutError:
            await self.bus.publish("approval.timeout", {"id": req.id}, source="approvals")
            return False
        finally:
            self.pending.pop(req.id, None)

    async def resolve(self, request_id: str, approved: bool, remember: bool = False) -> bool:
        """Called from the UI/voice layer when the user decides."""
        req = self.pending.get(request_id)
        if req is None or req.future.done():
            return False
        if approved and remember:
            self.grant_for_session(req.action)
        req.future.set_result(approved)
        await self.bus.publish(
            "approval.resolved", {"id": request_id, "approved": approved}, source="user"
        )
        return True
