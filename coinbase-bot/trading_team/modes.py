"""Trading mode state machine and absolute risk limits (Phase 10, hardened in Phase 14).

Three modes:
  PAPER            - simulated fills only (default).
  LIVE_MANUAL      - a real order may be sent, but only with a per-order
                     approval phrase from the user.
  LIVE_AUTONOMOUS  - fully prepared in Phase 14 but still LOCKED. Arming it
                     needs three things at once: a passing readiness report,
                     confirmed limits, and one exact activation phrase from
                     Nate. Nothing in this repository arms it on its own.

The absolute limits below are the user's. Agents may TIGHTEN them and may
always decide NO TRADE, but no code path here can raise them.

Phase 14 additions:
  * The emergency stop is persistent when a ``SafetyStore`` is attached. A
    restart does not clear it, and an unreadable stop file counts as STOP.
  * Daily and total realised-loss ceilings are enforced from the durable
    ledger, so they keep counting across restarts.
  * Slippage is checked against the configured ceiling before an order.
  * Only products on the allow-list may be traded.
  * A controller WITHOUT a store is in-memory only. That is fine for paper and
    for tests, and the readiness check refuses live trading in that state.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal as D
from enum import Enum
from typing import Optional

from .persistence import SafetyStore

#: The one phrase that arms autonomous live trading. Nothing else does.
AUTONOMOUS_ACTIVATION_PHRASE = "AUTONOMES LIVE TRADING AKTIVIEREN 17.10 USDC"


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
        for field_name, value in kw.items():
            if field_name == "confirmed":
                raise ModeError("confirmed cannot be changed by tightening")
            current = getattr(self, field_name)
            out[field_name] = min(D(str(value)), current)
        return replace(self, **out)

    def is_complete(self) -> bool:
        """True when every ceiling the user must set is a positive number."""
        return (
            self.total_capital_usdc > 0
            and self.max_daily_loss_usdc > 0
            and self.max_total_loss_usdc > 0
            and self.max_open_exposure_usdc > 0
        )


@dataclass
class ModeController:
    """Owns the current mode. Live execution always needs more than a flag."""

    limits: AbsoluteLimits
    mode: TradingMode = TradingMode.PAPER
    store: Optional[SafetyStore] = None
    allowed_products: tuple = ("BTC-USDC", "ETH-USDC", "SOL-USDC")
    _memory_stop: bool = False
    _stop_reason: str = ""
    _autonomous_armed: bool = False
    _armed_note: str = ""
    _tighten_log: list = field(default_factory=list)

    # ---- emergency stop (persistent when a store is attached) ------------

    @property
    def persistent(self) -> bool:
        """True when the emergency stop and the loss ledger survive a restart."""
        return self.store is not None

    @property
    def emergency_stop(self) -> bool:
        if self.store is None:
            return self._memory_stop
        return self.store.read_emergency_stop().active

    @property
    def stop_reason(self) -> str:
        if self.store is None:
            return self._stop_reason
        return self.store.read_emergency_stop().reason

    def trigger_emergency_stop(self, reason: str, source: str = "system") -> None:
        """Stop everything and fall back to PAPER. With a store attached this
        is written to disk before returning, so a crash right after cannot
        lose it."""
        if self.store is not None:
            self.store.trigger_stop(reason, source=source)
        self._memory_stop = True
        self._stop_reason = reason
        self._autonomous_armed = False
        self._armed_note = f"entwaffnet durch Not-Aus: {reason}"
        self.mode = TradingMode.PAPER

    def clear_emergency_stop(self, cleared_by: str = "", reason: str = "") -> None:
        """Clearing is a deliberate human act. With a store attached both the
        person and the reason are required and recorded."""
        if self.store is not None:
            if not cleared_by.strip() or not reason.strip():
                raise ModeError(
                    "Not-Aus loeschen verlangt 'cleared_by' und eine Begruendung."
                )
            self.store.clear_stop(cleared_by, reason)
        self._memory_stop = False
        self._stop_reason = ""

    # ---- loss ceilings ---------------------------------------------------

    def loss_state(self) -> dict:
        """Realised losses from the durable ledger, as positive numbers."""
        if self.store is None:
            return {"daily_loss": D("0"), "total_loss": D("0"), "persistent": False}
        ledger = self.store.read_ledger()
        return {
            "daily_loss": ledger.daily_loss(),
            "total_loss": ledger.total_loss(),
            "persistent": True,
        }

    def loss_breach(self) -> Optional[str]:
        """Return the breached ceiling, or None. Checked before every order."""
        state = self.loss_state()
        if state["daily_loss"] >= self.limits.max_daily_loss_usdc > 0:
            return (
                f"Tagesverlust {state['daily_loss']} USDC erreicht die Grenze "
                f"{self.limits.max_daily_loss_usdc} USDC"
            )
        if state["total_loss"] >= self.limits.max_total_loss_usdc > 0:
            return (
                f"Gesamtverlust {state['total_loss']} USDC erreicht die Grenze "
                f"{self.limits.max_total_loss_usdc} USDC"
            )
        return None

    def book_realised(self, amount: D) -> Optional[str]:
        """Record a closed round trip and trip the emergency stop when a loss
        ceiling is now breached. Returns the breach message, or None."""
        if self.store is None:
            raise ModeError("Verlustbuchung verlangt einen persistenten SafetyStore.")
        self.store.book_realised(D(str(amount)))
        breach = self.loss_breach()
        if breach:
            self.trigger_emergency_stop(
                f"Verlustgrenze erreicht: {breach}", source="risk-gate"
            )
        return breach

    # ---- tightening (agents may narrow, never widen) ---------------------

    def tighten(self, who: str, **kw) -> AbsoluteLimits:
        """Apply a RiskManager tightening. Any attempt to raise is clamped by
        ``AbsoluteLimits.tightened`` and the attempt is logged."""
        before = self.limits
        self.limits = before.tightened(**kw)
        for name, value in kw.items():
            requested = D(str(value))
            applied = getattr(self.limits, name)
            self._tighten_log.append(
                {
                    "who": who,
                    "field": name,
                    "requested": str(requested),
                    "applied": str(applied),
                    "clamped": requested > getattr(before, name),
                }
            )
        return self.limits

    @property
    def tighten_log(self) -> list:
        return list(self._tighten_log)

    # ---- mode transitions ------------------------------------------------

    def set_mode(self, mode: TradingMode) -> None:
        if self.emergency_stop:
            raise ModeError(f"Not-Aus aktiv: {self.stop_reason}")
        if mode is TradingMode.LIVE_AUTONOMOUS:
            if not self._autonomous_armed:
                raise ModeError(
                    "LIVE AUTONOMOUS ist gesperrt. Dafuer braucht es eine bestandene "
                    "Bereitschaftspruefung und die ausdrueckliche Aktivierungsfreigabe "
                    "von Nate (arm_autonomous)."
                )
            breach = self.loss_breach()
            if breach:
                raise ModeError(f"Verlustgrenze erreicht: {breach}")
            self.mode = mode
            return
        if mode is TradingMode.LIVE_MANUAL and not (
            self.limits.confirmed and self.limits.is_complete()
        ):
            raise ModeError(
                "LIVE MANUAL verlangt bestaetigte, vollstaendige Risikolimits."
            )
        self.mode = mode

    # ---- arming autonomous live (deliberately hard) ----------------------

    def arm_autonomous(
        self, activation_phrase: str, readiness_passed: bool, armed_by: str = ""
    ) -> None:
        """Arm autonomous live trading.

        Every condition must hold at the same time:
          * no emergency stop,
          * a persistent store (an autonomous bot without durable state is not
            allowed to trade),
          * confirmed and complete limits,
          * a readiness report that passed every criterion,
          * the exact activation phrase, and a named person.

        This method is never called anywhere in this repository. It exists so
        that Nate can arm the system in one explicit step once he decides to.
        """
        if self.emergency_stop:
            raise ModeError(f"Not-Aus aktiv: {self.stop_reason}")
        if self.store is None:
            raise ModeError(
                "Autonomer Live-Betrieb verlangt einen persistenten SafetyStore."
            )
        if not (self.limits.confirmed and self.limits.is_complete()):
            raise ModeError("Risikolimits nicht bestaetigt oder unvollstaendig.")
        if not readiness_passed:
            raise ModeError("Bereitschaftspruefung nicht bestanden.")
        breach = self.loss_breach()
        if breach:
            raise ModeError(f"Verlustgrenze erreicht: {breach}")
        if activation_phrase != AUTONOMOUS_ACTIVATION_PHRASE:
            raise ModeError("Aktivierungsfreigabe fehlt oder stimmt nicht exakt.")
        if not armed_by.strip():
            raise ModeError("Aktivierung verlangt eine namentliche Freigabe.")
        self._autonomous_armed = True
        self._armed_note = f"scharfgeschaltet von {armed_by}"

    def disarm_autonomous(self, reason: str = "manuell") -> None:
        self._autonomous_armed = False
        self._armed_note = f"entwaffnet: {reason}"
        if self.mode is TradingMode.LIVE_AUTONOMOUS:
            self.mode = TradingMode.PAPER

    @property
    def autonomous_armed(self) -> bool:
        return self._autonomous_armed

    # ---- execution gate --------------------------------------------------

    def approval_phrase(self, side: str, product_id: str, size: str) -> str:
        return f"LIVE {side.upper()} {product_id} {size}"

    def may_execute_live(
        self,
        side: str,
        product_id: str,
        size: str,
        approval: Optional[str] = None,
        expected_slippage_pct: Optional[D] = None,
        notional_usdc: Optional[D] = None,
        open_exposure_usdc: D = D("0"),
    ) -> tuple:
        """Every condition must hold. Returns (allowed, reason).

        The checks run in the order a failure matters: stop first, then mode,
        then limits, then the order itself.
        """
        if self.emergency_stop:
            return False, f"Not-Aus aktiv: {self.stop_reason}"
        if self.mode is TradingMode.PAPER:
            return False, "Modus PAPER - keine echte Order"
        if not self.limits.confirmed or not self.limits.is_complete():
            return False, "Risikolimits nicht bestaetigt"
        if product_id not in self.allowed_products:
            return False, f"Produkt {product_id} steht nicht auf der Freigabeliste"

        breach = self.loss_breach()
        if breach:
            return False, f"Verlustgrenze erreicht: {breach}"

        if expected_slippage_pct is not None:
            slip = D(str(expected_slippage_pct))
            if slip > self.limits.max_slippage_pct:
                return False, (
                    f"Erwartete Slippage {slip}% ueber der Grenze "
                    f"{self.limits.max_slippage_pct}%"
                )

        if notional_usdc is not None:
            notional = D(str(notional_usdc))
            room = self.max_position_usdc(notional, open_exposure_usdc)
            if notional > room:
                return False, (
                    f"Ordergroesse {notional} USDC ueber dem erlaubten "
                    f"Rahmen {room} USDC"
                )

        if self.mode is TradingMode.LIVE_AUTONOMOUS:
            if not self._autonomous_armed:
                return False, "LIVE AUTONOMOUS nicht scharfgeschaltet"
            if self.store is None:
                return False, "Autonomer Betrieb ohne persistenten Zustand"
            return True, "Freigegeben (LIVE AUTONOMOUS, scharfgeschaltet)"

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
        losses = self.loss_state()
        return {
            "mode": self.mode.value,
            "emergency_stop": self.emergency_stop,
            "emergency_stop_reason": self.stop_reason,
            "emergency_stop_persistent": self.persistent,
            "live_execution_tested": True,  # proven by the Phase 3 round trip
            "autonomous_live_locked": not self._autonomous_armed,
            "autonomous_note": self._armed_note,
            "risk_limits_configured": self.limits.confirmed
            and self.limits.is_complete(),
            "daily_loss_usdc": str(losses["daily_loss"]),
            "total_loss_usdc": str(losses["total_loss"]),
            "max_daily_loss_usdc": str(self.limits.max_daily_loss_usdc),
            "max_total_loss_usdc": str(self.limits.max_total_loss_usdc),
            "max_slippage_pct": str(self.limits.max_slippage_pct),
            "allowed_products": list(self.allowed_products),
        }
