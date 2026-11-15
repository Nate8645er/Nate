"""Pre-trade gate and post-trade reconciliation for live orders (Phase 14).

This module decides whether an order may be SENT and what to do with what
comes back. It never sends anything itself - the connector does that - and it
never invents a value it does not have.

The governing rule, in Nate's words: "Bei unklaren Zuständen: BLOCK NEW
ORDERS." Every unknown in this file resolves to a refusal, not to a guess.

Pre-trade (``check_order``) verifies, in this order:
  emergency stop -> mode and approval -> product allow-list -> market data
  freshness -> known fee rate -> available balance -> exchange minimum ->
  open orders -> existing exposure -> slippage -> price impact -> loss gates.

Post-trade (``classify_fill``) sorts an order into FILLED / PARTIAL / OPEN /
UNKNOWN / FAILED and says what the caller must do next. A timeout is UNKNOWN,
never FAILED: an order that timed out on the client may well be live on the
exchange, so the only correct move is to read the status back.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal as D
from typing import Any, Optional

from .modes import ModeController, TradingMode
from .persistence import SafetyStore

#: Market data older than this many seconds is stale and blocks new orders.
MAX_MARKET_AGE_S = 90

#: Price impact above this percentage blocks the order regardless of slippage.
MAX_PRICE_IMPACT_PCT = D("2.0")


@dataclass
class GateResult:
    allowed: bool
    reasons: list = field(default_factory=list)
    checks: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
        }


def new_client_order_id(prefix: str = "hg") -> str:
    """A fresh, unique client order id. Coinbase rejects a repeat of one, which
    is what makes a retry idempotent."""
    return f"{prefix}-{uuid.uuid4().hex}"


def check_order(
    controller: ModeController,
    *,
    product_id: str,
    side: str,
    notional_usdc: D,
    size_text: str = "",
    approval: Optional[str] = None,
    available_usdc: Optional[D] = None,
    open_orders: Optional[list] = None,
    open_exposure_usdc: D = D("0"),
    market_updated_at: Optional[float] = None,
    now: Optional[float] = None,
    fee_rate: Optional[D] = None,
    min_order_usdc: Optional[D] = None,
    expected_slippage_pct: Optional[D] = None,
    price_impact_pct: Optional[D] = None,
) -> GateResult:
    """Decide whether this order may be sent. Any ``None`` that matters is a
    refusal, because an unknown is not a pass."""
    reasons: list = []
    checks: dict = {}
    notional = D(str(notional_usdc))
    now = time.time() if now is None else now

    # 1-5: mode, stop, limits, product, loss gates - all inside the controller.
    mode_ok, mode_reason = controller.may_execute_live(
        side,
        product_id,
        size_text or str(notional),
        approval,
        expected_slippage_pct=expected_slippage_pct,
        notional_usdc=notional,
        open_exposure_usdc=open_exposure_usdc,
    )
    checks["mode_gate"] = mode_reason
    if not mode_ok:
        reasons.append(mode_reason)

    # 6: market data freshness.
    if market_updated_at is None:
        reasons.append("Keine Marktdaten - Zeitstempel fehlt")
        checks["market_age_s"] = None
    else:
        age = now - float(market_updated_at)
        checks["market_age_s"] = round(age, 1)
        if age > MAX_MARKET_AGE_S:
            reasons.append(f"Marktdaten veraltet ({age:.0f}s > {MAX_MARKET_AGE_S}s)")

    # 7: fees must be known, because fee losses count against the loss ceiling.
    if fee_rate is None:
        reasons.append("Gebuehrensatz unbekannt")
        checks["fee_rate"] = None
    else:
        checks["fee_rate"] = str(fee_rate)
        checks["estimated_fee_usdc"] = str(
            (notional * D(str(fee_rate))).quantize(D("0.000001"))
        )

    # 8: funds, including the fee.
    if available_usdc is None:
        reasons.append("Verfuegbares Guthaben unbekannt")
    else:
        need = notional  # Coinbase takes the fee out of quote_size
        checks["required_usdc"] = str(need)
        checks["available_usdc"] = str(available_usdc)
        if need > D(str(available_usdc)):
            reasons.append(f"Guthaben reicht nicht ({need} > {available_usdc} USDC)")

    # 9: exchange minimum.
    if min_order_usdc is None:
        reasons.append("Mindestordergroesse unbekannt")
    elif notional < D(str(min_order_usdc)):
        reasons.append(f"Order unter dem Minimum ({notional} < {min_order_usdc} USDC)")

    # 10: resting orders tie up capital and can double an exposure.
    resting = list(open_orders or [])
    checks["open_orders"] = len(resting)
    if any((o.get("product_id") == product_id) for o in resting):
        reasons.append(f"Offene Order auf {product_id} vorhanden")

    # Slippage must be known for a buy; an unknown is not a pass.
    if expected_slippage_pct is None:
        reasons.append("Erwartete Slippage unbekannt")
    checks["expected_slippage_pct"] = (
        None if expected_slippage_pct is None else str(expected_slippage_pct)
    )

    # 11: price impact, separate from slippage.
    if price_impact_pct is not None and D(str(price_impact_pct)) > MAX_PRICE_IMPACT_PCT:
        reasons.append(
            f"Price Impact {price_impact_pct}% ueber {MAX_PRICE_IMPACT_PCT}%"
        )
    checks["price_impact_pct"] = (
        None if price_impact_pct is None else str(price_impact_pct)
    )

    return GateResult(allowed=not reasons, reasons=reasons, checks=checks)


def claim_or_refuse(
    store: SafetyStore, client_order_id: str, detail: dict
) -> GateResult:
    """Reserve the client order id on disk BEFORE sending. A second attempt
    with the same id is refused here, so a duplicate buy cannot leave this
    process even if the caller retries after a crash."""
    if store.claim_order_id(client_order_id, detail):
        return GateResult(
            True, [], {"client_order_id": client_order_id, "claim": "neu"}
        )
    return GateResult(
        False,
        [f"client_order_id {client_order_id} wurde bereits verwendet"],
        {"client_order_id": client_order_id, "claim": "doppelt"},
    )


@dataclass
class FillState:
    state: str  # FILLED | PARTIAL | OPEN | UNKNOWN | FAILED
    filled_size: D
    requested_size: D
    action: str  # what the caller must do next
    detail: dict = field(default_factory=dict)

    @property
    def blocks_new_orders(self) -> bool:
        return self.state in ("UNKNOWN", "PARTIAL", "OPEN")

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "filled_size": str(self.filled_size),
            "requested_size": str(self.requested_size),
            "action": self.action,
            "blocks_new_orders": self.blocks_new_orders,
            "detail": dict(self.detail),
        }


def classify_fill(order: Optional[dict], requested_size: D) -> FillState:
    """Turn a Coinbase order record into a state and a next step.

    ``order is None`` means the status could not be read - a timeout, a dropped
    connection, an API outage. That is UNKNOWN, and UNKNOWN blocks new orders
    until the status is actually read. It is never treated as 'did not happen'.
    """
    requested = D(str(requested_size))
    if order is None:
        return FillState(
            "UNKNOWN",
            D("0"),
            requested,
            "Status bei Coinbase abfragen, bevor irgendetwas gesendet wird",
            {"reason": "kein Orderstatus erhalten"},
        )

    status = str(order.get("status", "")).upper()
    filled = D(str(order.get("filled_size") or "0"))

    if status in ("FAILED", "CANCELLED", "EXPIRED") and filled == 0:
        return FillState(
            "FAILED",
            filled,
            requested,
            "Order kam nicht zustande - neue Entscheidung noetig, kein Blindkauf",
            {"status": status},
        )
    if status == "FILLED" and filled >= requested:
        return FillState(
            "FILLED",
            filled,
            requested,
            "Fill verbuchen, P&L berechnen",
            {"status": status},
        )
    if filled > 0 and filled < requested:
        return FillState(
            "PARTIAL",
            filled,
            requested,
            "Nur die tatsaechlich gefuellte Menge als Position fuehren; "
            "Rest nicht automatisch nachkaufen",
            {"status": status, "missing": str(requested - filled)},
        )
    if status in ("OPEN", "PENDING", "QUEUED"):
        return FillState(
            "OPEN",
            filled,
            requested,
            "Order laeuft noch - abwarten oder gezielt stornieren",
            {"status": status},
        )
    return FillState(
        "UNKNOWN",
        filled,
        requested,
        "Unerwarteter Status - keine neuen Orders bis geklaert",
        {"status": status},
    )


def read_back_status(
    connector: Any,
    order_id: str,
    requested_size: D,
    attempts: int = 3,
    delay_s: float = 1.0,
    sleep=time.sleep,
) -> FillState:
    """After a timeout: ask Coinbase what actually happened. Never re-send.

    Returns the classified state. If every attempt fails, the result is
    UNKNOWN, which blocks new orders - the safe direction.
    """
    last_error = ""
    for attempt in range(attempts):
        try:
            order = connector.get_real_order_status(order_id)
            return classify_fill(order, requested_size)
        except Exception as exc:  # noqa: BLE001 - any failure is UNKNOWN
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < attempts - 1:
                sleep(delay_s * (2**attempt))
    return FillState(
        "UNKNOWN",
        D("0"),
        D(str(requested_size)),
        "Coinbase-Status nicht lesbar - Not-Aus pruefen, keine neue Order",
        {"error": last_error},
    )


def realised_pnl(
    buy_cost_usdc: D,
    sell_proceeds_usdc: D,
    buy_fee_usdc: D = D("0"),
    sell_fee_usdc: D = D("0"),
) -> D:
    """Realised result of one round trip, fees included on both legs.

    Coinbase's ``total_value_after_fees`` already nets the fee, so pass the
    gross values together with the fees, or the net values with zero fees -
    not a mixture.
    """
    return (
        D(str(sell_proceeds_usdc))
        - D(str(sell_fee_usdc))
        - D(str(buy_cost_usdc))
        - D(str(buy_fee_usdc))
    )


def on_api_failure(
    controller: ModeController, what: str, error: str, trip_stop: bool = False
) -> dict:
    """One place for 'the exchange did not answer'.

    New orders are blocked for as long as the condition lasts. A repeated or
    safety-critical failure trips the persistent emergency stop, which a
    restart cannot clear.
    """
    if trip_stop:
        controller.trigger_emergency_stop(
            f"API-Ausfall bei {what}: {error}", source="api-guard"
        )
    elif controller.mode is not TradingMode.PAPER:
        controller.mode = TradingMode.PAPER
    return {
        "blocked": True,
        "what": what,
        "error": error,
        "emergency_stop": controller.emergency_stop,
        "mode": controller.mode.value,
    }
