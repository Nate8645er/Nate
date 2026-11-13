"""Trading mode state machine and absolute risk limits (Phase 10).

Three modes:
  PAPER            - simulated fills only (default).
  LIVE_MANUAL      - a real order may be sent, but only with a per-order
                     approval phrase from the user.
  LIVE_AUTONOMOUS  - LOCKED. Requires a separate, explicit confirmation of the
                     final risk configuration before it can ever be selected.

The absolute limits below are the user's. Agents may TIGHTEN them and may
always decide NO TRADE, but no code path here can raise them.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal as D
from enum import Enum
from typing import Optional


class TradingMode(Enum):
    PAPER = "PAPER"
    LIVE_MANUAL = "LIVE MANUAL"
    LIVE_AUTONOMOUS = "LIVE AUTONOMOUS"


class ModeError(RuntimeError):
    """A mode change or execution was refused."""


@dataclass(frozen=True)
class AbsoluteLimits:
    """Hard ceilings. `confirmed` is set only by an explicit user action."""
    total_capital_usdc: D = D("17.10")
    max_daily_loss_usdc: D = D("0")
    max_total_loss_usdc: D = D("0")
    max_slippage_pct: D = D("1.0")
    max_open_exposure_usdc: D = D("0")
    confirmed: bool = False

    def tightened(self, **kw) -> "AbsoluteLimits":
        """Return limits that are at most as permissive as these. Any attempt
        to raise a ceiling is clamped back to the current value."""
        out = {}
        for field, value in kw.items():
            if field == "confirmed":
                raise ModeError("confirmed cannot be changed by tightening")
            current = getattr(self, field)
            out[field] = min(D(str(value)), current)
        return replace(self, **out)

    def is_complete(self) -> bool:
        """True when every ceiling the user must set is a positive number."""
        return (self.total_capital_usdc > 0 and self.max_daily_loss_usdc > 0
                and self.max_total_loss_usdc > 0 and self.max_open_exposure_usdc > 0)


@dataclass
class ModeController:
    """Owns the current mode. Live execution always needs more than a flag."""

    limits: AbsoluteLimits
    mode: TradingMode = TradingMode.PAPER
    emergency_stop: bool = False
    _stop_reason: str = ""

    # ---- mode transitions ------------------------------------------------

    def set_mode(self, mode: TradingMode) -> None:
        if self.emergency_stop:
            raise ModeError(f"Not-Aus aktiv: {self._stop_reason}")
        if mode is TradingMode.LIVE_AUTONOMOUS:
            raise ModeError(
                "LIVE AUTONOMOUS ist gesperrt. Dafuer braucht es eine separate, "
                "ausdrueckliche Bestaetigung der endgueltigen Risikokonfiguration."
            )
        if mode is TradingMode.LIVE_MANUAL and not (self.limits.confirmed and self.limits.is_complete()):
            raise ModeError("LIVE MANUAL verlangt bestaetigte, vollstaendige Risikolimits.")
        self.mode = mode

    def trigger_emergency_stop(self, reason: str) -> None:
        self.emergency_stop = True
        self._stop_reason = reason
        self.mode = TradingMode.PAPER

    def clear_emergency_stop(self) -> None:
        self.emergency_stop = False
        self._stop_reason = ""

    # ---- execution gate --------------------------------------------------

    def approval_phrase(self, side: str, product_id: str, size: str) -> str:
        return f"LIVE {side.upper()} {product_id} {size}"

    def may_execute_live(self, side: str, product_id: str, size: str,
                         approval: Optional[str]) -> tuple:
        """Every condition must hold. Returns (allowed, reason)."""
        if self.emergency_stop:
            return False, f"Not-Aus aktiv: {self._stop_reason}"
        if self.mode is TradingMode.PAPER:
            return False, "Modus PAPER - keine echte Order"
        if self.mode is TradingMode.LIVE_AUTONOMOUS:
            return False, "LIVE AUTONOMOUS gesperrt"
        if not self.limits.confirmed or not self.limits.is_complete():
            return False, "Risikolimits nicht bestaetigt"
        expected = self.approval_phrase(side, product_id, size)
        if approval != expected:
            return False, "Freigabe fehlt oder passt nicht exakt zur Order"
        return True, "Freigegeben (LIVE MANUAL, Einzelfreigabe)"

    # ---- sizing ----------------------------------------------------------

    def max_position_usdc(self, available_usdc: D, open_exposure_usdc: D = D("0")) -> D:
        """Largest position allowed now: never above the capital ceiling, never
        above what is actually available, and never beyond open-exposure room."""
        room = self.limits.total_capital_usdc - open_exposure_usdc
        if self.limits.max_open_exposure_usdc > 0:
            room = min(room, self.limits.max_open_exposure_usdc - open_exposure_usdc)
        return max(D("0"), min(available_usdc, room))

    def status(self) -> dict:
        return {
            "mode": self.mode.value,
            "emergency_stop": self.emergency_stop,
            "live_execution_tested": True,       # proven by the Phase 3 round trip
            "autonomous_live_locked": True,
            "risk_limits_configured": self.limits.confirmed and self.limits.is_complete(),
        }
