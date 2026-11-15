"""Durable safety state for live trading (Phase 14).

Everything in this module must survive a process restart, a crash and a reboot.
A risk gate that forgets what happened is not a risk gate.

Three records live here:

  * ``emergency_stop``  - once set, it stays set until a human clears it with an
    explicit reason. A restart does NOT clear it.
  * ``loss ledger``     - realised profit and loss per UTC day plus the running
    total, so the daily and total loss ceilings keep counting across restarts.
  * ``order ledger``    - every client_order_id this system has ever submitted,
    so the same order can never be sent twice after a crash mid-flight.

Writes are atomic (temp file + ``os.replace``) so a crash during a write leaves
either the old file or the new one, never half of either.

No API keys, no secrets and no personal data are stored here. The directory is
gitignored.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from typing import Optional

DEFAULT_STATE_DIR = Path(__file__).resolve().parent.parent / "state"

_LOCK = threading.RLock()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_day(moment: Optional[datetime] = None) -> str:
    return (moment or _utc_now()).strftime("%Y-%m-%d")


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _read_json(path: Path) -> dict:
    """Read a state file. A missing file is empty state. A corrupted file
    raises - treating it as empty would be a fail-open for the emergency stop."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


@dataclass
class EmergencyStop:
    active: bool = False
    reason: str = ""
    since: str = ""
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "active": self.active,
            "reason": self.reason,
            "since": self.since,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmergencyStop":
        return cls(
            active=bool(data.get("active", False)),
            reason=str(data.get("reason", "")),
            since=str(data.get("since", "")),
            source=str(data.get("source", "")),
        )


@dataclass
class LossLedger:
    """Realised P&L. Losses are negative numbers; the ceilings are compared
    against their absolute value."""

    total_realised: D = D("0")
    per_day: dict = field(default_factory=dict)

    def realised_today(self, day: Optional[str] = None) -> D:
        return D(str(self.per_day.get(day or _utc_day(), "0")))

    def daily_loss(self, day: Optional[str] = None) -> D:
        """Loss booked today as a positive number (0 when today is profitable)."""
        return max(D("0"), -self.realised_today(day))

    def total_loss(self) -> D:
        """Loss booked in total as a positive number (0 when overall profitable)."""
        return max(D("0"), -self.total_realised)

    def to_dict(self) -> dict:
        return {
            "total_realised": str(self.total_realised),
            "per_day": {day: str(value) for day, value in self.per_day.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LossLedger":
        return cls(
            total_realised=D(str(data.get("total_realised", "0"))),
            per_day=dict(data.get("per_day") or {}),
        )


class SafetyStore:
    """Single owner of the durable safety files.

    Used by ``trading_team.modes.ModeController`` (emergency stop, loss gates)
    and by the execution path (order dedup). The FastAPI backend in
    ``server/app.py`` reaches it through the ModeController, never directly.
    """

    def __init__(self, state_dir: Path | str = DEFAULT_STATE_DIR):
        self.dir = Path(state_dir)
        self.stop_path = self.dir / "emergency_stop.json"
        self.ledger_path = self.dir / "loss_ledger.json"
        self.orders_path = self.dir / "order_ledger.json"
        self.load_errors: list[str] = []

    # ---- emergency stop --------------------------------------------------

    def read_emergency_stop(self) -> EmergencyStop:
        """A corrupted or unreadable stop file is treated as STOP ACTIVE.
        Failing closed is the only safe reading of 'I cannot tell'."""
        try:
            data = _read_json(self.stop_path)
        except (OSError, ValueError) as exc:
            self.load_errors.append(f"emergency_stop.json unlesbar: {exc}")
            return EmergencyStop(
                active=True,
                reason="Not-Aus-Datei unlesbar - fail-closed",
                since=_utc_now().isoformat(),
                source="store",
            )
        if not data:
            return EmergencyStop()
        return EmergencyStop.from_dict(data)

    def write_emergency_stop(self, stop: EmergencyStop) -> None:
        with _LOCK:
            _atomic_write_json(self.stop_path, stop.to_dict())

    def trigger_stop(self, reason: str, source: str = "system") -> EmergencyStop:
        stop = EmergencyStop(
            active=True, reason=reason, since=_utc_now().isoformat(), source=source
        )
        self.write_emergency_stop(stop)
        return stop

    def clear_stop(self, cleared_by: str, reason: str) -> EmergencyStop:
        if not cleared_by.strip() or not reason.strip():
            raise ValueError("Not-Aus loeschen verlangt Person und Begruendung.")
        stop = EmergencyStop(
            active=False,
            reason=f"geloescht von {cleared_by}: {reason}",
            since=_utc_now().isoformat(),
            source=cleared_by,
        )
        self.write_emergency_stop(stop)
        return stop

    # ---- loss ledger -----------------------------------------------------

    def read_ledger(self) -> LossLedger:
        try:
            return LossLedger.from_dict(_read_json(self.ledger_path))
        except (OSError, ValueError) as exc:
            self.load_errors.append(f"loss_ledger.json unlesbar: {exc}")
            raise

    def book_realised(self, amount: D, day: Optional[str] = None) -> LossLedger:
        """Record a realised result. Negative = loss. Called once per closed
        round trip, never on an unrealised mark."""
        with _LOCK:
            ledger = self.read_ledger()
            key = day or _utc_day()
            current = D(str(ledger.per_day.get(key, "0")))
            ledger.per_day[key] = str(current + D(str(amount)))
            ledger.total_realised = ledger.total_realised + D(str(amount))
            _atomic_write_json(self.ledger_path, ledger.to_dict())
            return ledger

    # ---- order dedup -----------------------------------------------------

    def read_order_ids(self) -> dict:
        try:
            return dict(_read_json(self.orders_path))
        except (OSError, ValueError) as exc:
            self.load_errors.append(f"order_ledger.json unlesbar: {exc}")
            raise

    def claim_order_id(self, client_order_id: str, detail: dict) -> bool:
        """Reserve a client_order_id BEFORE the order is sent.

        Returns True when this id is new (caller may send), False when it was
        already used (caller must not send). The claim is written to disk
        before the network call, so a crash between claim and send still
        blocks the retry - which is the safe direction.
        """
        with _LOCK:
            known = self.read_order_ids()
            if client_order_id in known:
                return False
            known[client_order_id] = {
                "claimed_at": _utc_now().isoformat(),
                **detail,
            }
            _atomic_write_json(self.orders_path, known)
            return True

    def order_count(self) -> int:
        return len(self.read_order_ids())

    # ---- diagnostics -----------------------------------------------------

    def snapshot(self) -> dict:
        stop = self.read_emergency_stop()
        try:
            ledger = self.read_ledger()
            ledger_view = {
                "total_realised": str(ledger.total_realised),
                "daily_loss": str(ledger.daily_loss()),
                "total_loss": str(ledger.total_loss()),
                "days_recorded": len(ledger.per_day),
            }
        except (OSError, ValueError) as exc:
            ledger_view = {"error": str(exc)}
        try:
            orders = self.order_count()
        except (OSError, ValueError) as exc:
            orders = f"error: {exc}"
        return {
            "state_dir": str(self.dir),
            "emergency_stop": stop.to_dict(),
            "ledger": ledger_view,
            "orders_claimed": orders,
            "load_errors": list(self.load_errors),
        }
