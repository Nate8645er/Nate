"""The twelve-step live cycle (Phase 14). Prepared, not started.

    1 market analysis        5 RiskManager check      9 execution (gate open only)
    2 trading signal         6 Supervisor decision   10 Coinbase fill reconciliation
    3 team meeting           7 order preview         11 trade review
    4 joint discussion       8 final safety check    12 portfolio update

Steps 1-6 are the existing ``hold_meeting``. This module adds 7-12 around the
existing connector. Nothing here runs on its own: ``run_cycle`` must be called,
and it sends an order only when the ModeController's gate is open - which in
this repository it never is, because autonomous mode is not armed anywhere.

Rules that hold in every branch:
  * A meeting alone never sends an order. The order is rebuilt from the
    meeting record and re-checked (``ticket_from_meeting``); a record that was
    altered after the meeting is refused.
  * A RiskManager veto is final.
  * Unknown balance, fee, minimum, slippage or market age blocks the order.
  * The client order id is written to disk before the order is sent. After a
    timeout the status is read back; the order is never re-sent blindly.
  * A partial fill is booked at the filled amount only.
  * Fees are part of the realised result that counts against the loss limits.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from decimal import Decimal as D
from pathlib import Path
from typing import Any, Optional

from .core import RiskManager
from .execution_guard import (
    check_order,
    claim_or_refuse,
    classify_fill,
    new_client_order_id,
)
from .meeting import Decision, MeetingResult, hold_meeting
from .modes import ModeController, TradingMode
from .persistence import SafetyStore, _atomic_write_json, _read_json

REQUIRED_AGENTS = (
    "MarketAnalyst",
    "Strategist",
    "RiskManager",
    "Supervisor",
    "ExecutionAgent",
    "TradeReviewer",
)


def _phrase(side: str, product_id: str, size: str) -> str:
    """Same text as coinbase_connector.connector.confirmation_phrase."""
    return f"EXECUTE {side.upper()} {product_id} {size}"


@dataclass
class Ticket:
    ok: bool
    reasons: list = field(default_factory=list)
    side: str = ""
    product_id: str = ""
    quote_size: D = D("0")
    stop_loss: str = ""
    take_profit: str = ""


def ticket_from_meeting(
    result: MeetingResult,
    controller: ModeController,
    available_usdc: D,
    open_exposure_usdc: D = D("0"),
) -> Ticket:
    """Rebuild the order from the meeting record and verify every link.

    This is the defence against a manipulated agent decision: the prepared
    order must agree with what the RiskManager approved, with the controller's
    own ceiling, and with the approval phrase computed during the meeting.
    """
    reasons = []
    if result.final not in (Decision.BUY, Decision.SELL):
        reasons.append(f"Meeting-Ergebnis ist {result.final.value}, keine Order")
    if any(s.decision is Decision.VETO for s in result.statements):
        reasons.append("Im Protokoll steht ein Veto")
    if not result.agreed:
        reasons.append("Kein Konsens im Meeting")
    present = {s.agent for s in result.statements}
    missing = [a for a in REQUIRED_AGENTS if a not in present]
    if missing:
        reasons.append("Meeting unvollstaendig, es fehlen: " + ", ".join(missing))
    order = result.prepared_order
    if not order:
        reasons.append("Keine vorbereitete Order im Protokoll")
        return Ticket(False, reasons)

    side, product = str(order.get("side", "")), str(order.get("product_id", ""))
    try:
        size = D(str(order.get("quote_size")))
    except Exception:  # noqa: BLE001
        return Ticket(False, reasons + ["Ordergroesse nicht lesbar"])
    if product != result.symbol:
        reasons.append("Produkt der Order weicht vom Meeting ab")
    if side != result.final.value:
        reasons.append("Seite der Order weicht von der Entscheidung ab")
    approved = [
        s
        for s in result.statements
        if s.agent == "RiskManager" and "quote_size" in s.data
    ]
    if not approved:
        reasons.append("Keine Groessenfreigabe des RiskManagers im Protokoll")
    elif size > D(str(approved[-1].data["quote_size"])):
        reasons.append("Order groesser als vom RiskManager freigegeben")
    if size > controller.max_position_usdc(D(str(available_usdc)), open_exposure_usdc):
        reasons.append("Order groesser als der erlaubte Rahmen")
    if order.get("approval_phrase") != controller.approval_phrase(
        side, product, str(size)
    ):
        reasons.append("Freigabetext passt nicht zur Order (Protokoll veraendert?)")
    return Ticket(
        not reasons,
        reasons,
        side,
        product,
        size,
        str(order.get("stop_loss", "")),
        str(order.get("take_profit", "")),
    )


# ---- durable positions, meeting log, unresolved orders --------------------


def read_positions(store: SafetyStore) -> dict:
    return dict(_read_json(store.dir / "positions.json"))


def write_positions(store: SafetyStore, positions: dict) -> None:
    _atomic_write_json(store.dir / "positions.json", positions)


def log_meeting(store: SafetyStore, record: dict) -> None:
    path = Path(store.dir) / "live_meetings.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def unresolved_orders(store: SafetyStore) -> list:
    """Claimed order ids with no recorded outcome - e.g. the backend died
    between sending and reading the fill. They block new orders until
    ``resolve_unresolved`` has asked Coinbase what happened."""
    return [
        cid for cid, row in store.read_order_ids().items() if not row.get("outcome")
    ]


def _set_outcome(store: SafetyStore, client_order_id: str, outcome: dict) -> None:
    orders = store.read_order_ids()
    orders.setdefault(client_order_id, {})["outcome"] = outcome
    _atomic_write_json(store.orders_path, orders)


def _read_order(connector: Any, order_id: str, attempts: int = 3) -> Optional[dict]:
    """Read an order back. None means 'could not be read', never 'not there'."""
    for _ in range(attempts):
        try:
            return connector.get_real_order_status(order_id)
        except Exception:  # noqa: BLE001
            continue
    return None


def _slippage_pct(quote: dict, side: str) -> Optional[D]:
    try:
        bid, ask = D(str(quote["bid"])), D(str(quote["ask"]))
    except Exception:  # noqa: BLE001
        return None
    if bid <= 0 or ask <= 0:
        return None
    mid = (bid + ask) / 2
    edge = ask if side == "BUY" else bid
    return abs(edge - mid) / mid * 100


# ---- the cycle ------------------------------------------------------------


def run_cycle(
    symbol: str,
    closes: list,
    *,
    controller: ModeController,
    risk: RiskManager,
    connector: Any,
    store: SafetyStore,
    market_updated_at: Optional[float],
    fee_rate: Optional[D],
    min_order_usdc: Optional[D],
    approval: Optional[str] = None,
    open_orders: Optional[list] = None,
    now: Optional[float] = None,
) -> dict:
    """One full cycle for one product. Returns a record of every step."""
    out: dict = {
        "symbol": symbol,
        "ts": time.time() if now is None else now,
        "mode": controller.mode.value,
        "sent": False,
        "steps": {},
    }

    def finish(note: str) -> dict:
        out["result"] = note
        log_meeting(store, out)
        return out

    pending = unresolved_orders(store)
    if pending:
        return finish(
            f"BLOCKIERT: ungeklaerte Order(s) {pending} - erst Status abgleichen"
        )

    try:
        available = D(str(connector.get_available_funds("USDC")))
        if open_orders is None:
            open_orders = connector.get_open_orders()
    except Exception as exc:  # noqa: BLE001
        return finish(f"BLOCKIERT: Coinbase nicht lesbar ({type(exc).__name__})")

    positions = read_positions(store)
    exposure = sum((D(str(p["cost_usdc"])) for p in positions.values()), D("0"))

    # 1-6: the existing meeting.
    meeting = hold_meeting(
        symbol,
        closes,
        risk=risk,
        controller=controller,
        available_usdc=available,
        open_exposure_usdc=exposure,
        approval=approval,
        fee_rate=fee_rate if fee_rate is not None else D("0.001"),
        min_order_usdc=min_order_usdc if min_order_usdc is not None else D("1"),
    )
    out["meeting"] = meeting.to_dict()
    ticket = ticket_from_meeting(meeting, controller, available, exposure)
    out["steps"]["ticket"] = {"ok": ticket.ok, "reasons": ticket.reasons}
    if not ticket.ok:
        return finish("NO TRADE: " + "; ".join(ticket.reasons))
    if ticket.side != "BUY":
        return finish("NO TRADE: Verkaeufe laufen ueber close_position")
    if symbol in positions:
        return finish("NO TRADE: Position besteht bereits")

    # 7: preview and price.
    try:
        quote = connector.get_market_price(symbol)
        preview = connector.preview_buy_order(symbol, str(ticket.quote_size))
    except Exception as exc:  # noqa: BLE001
        return finish(
            f"BLOCKIERT: Vorschau fehlgeschlagen ({type(exc).__name__}: {exc})"
        )
    slippage = _slippage_pct(quote, "BUY")
    out["steps"]["preview"] = {
        "slippage_pct": None if slippage is None else str(slippage),
        "preview_keys": sorted(preview)[:12],
    }

    # 8: final safety check.
    gate = check_order(
        controller,
        product_id=symbol,
        side="BUY",
        notional_usdc=ticket.quote_size,
        size_text=str(ticket.quote_size),
        approval=approval,
        available_usdc=available,
        open_orders=open_orders,
        open_exposure_usdc=exposure,
        market_updated_at=market_updated_at,
        now=now,
        fee_rate=fee_rate,
        min_order_usdc=min_order_usdc,
        expected_slippage_pct=slippage,
    )
    out["steps"]["gate"] = gate.to_dict()
    if not gate.allowed:
        return finish("NICHT GESENDET: " + "; ".join(gate.reasons))

    cid = new_client_order_id()
    claim = claim_or_refuse(
        store,
        cid,
        {"product_id": symbol, "side": "BUY", "quote_size": str(ticket.quote_size)},
    )
    if not claim.allowed:
        return finish("NICHT GESENDET: " + "; ".join(claim.reasons))

    # 9: execution.
    try:
        created = connector.execute_real_buy(
            symbol,
            str(ticket.quote_size),
            cid,
            _phrase("BUY", symbol, str(ticket.quote_size)),
        )
        order_id = created["order_id"]
        out["sent"] = True
    except TimeoutError as exc:
        # The order may exist on the exchange. Nothing is re-sent; the claim
        # stays unresolved and blocks every further order.
        controller.trigger_emergency_stop(
            f"Orderstatus unbekannt nach Timeout ({cid})", source="pipeline"
        )
        out["steps"]["send_error"] = f"Timeout: {exc}"
        return finish(
            "UNBEKANNT: Timeout beim Senden - Not-Aus gesetzt, kein erneuter Kauf"
        )
    except Exception as exc:  # noqa: BLE001
        _set_outcome(
            store, cid, {"state": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
        )
        return finish(f"NICHT AUSGEFUEHRT: {type(exc).__name__}: {exc}")

    # 10-12: reconciliation, review, portfolio.
    order = _read_order(connector, order_id)
    return finish(_book_buy(out, store, controller, cid, order_id, order, ticket))


def _book_buy(
    out: dict,
    store: SafetyStore,
    controller: ModeController,
    cid: str,
    order_id: str,
    order: Optional[dict],
    ticket: Ticket,
) -> str:
    if order is None:
        controller.trigger_emergency_stop(
            f"Orderstatus nicht lesbar ({order_id})", source="pipeline"
        )
        return "UNBEKANNT: Status nicht lesbar - Not-Aus gesetzt"
    filled = D(str(order.get("filled_size") or "0"))
    status = str(order.get("status", "")).upper()
    spent = D(str(order.get("total_value_after_fees") or "0"))
    fees = D(str(order.get("total_fees") or "0"))
    if status == "FILLED":
        state = "FILLED"
    elif status in ("FAILED", "CANCELLED", "EXPIRED"):
        state = "PARTIAL" if filled > 0 else "FAILED"
    else:
        state = "OPEN"
    out["steps"]["fill"] = {
        "state": state,
        "filled_size": str(filled),
        "spent_usdc": str(spent),
        "fees_usdc": str(fees),
        "order_id": order_id,
    }
    if state == "OPEN":
        return "OFFEN: Order noch nicht abgeschlossen - blockiert bis geklaert"
    if state == "FAILED":
        _set_outcome(store, cid, {"state": state, "order_id": order_id})
        return "FEHLGESCHLAGEN: keine Position, kein Nachkauf"
    positions = read_positions(store)
    positions[ticket.product_id] = {
        "base_size": str(filled),
        "cost_usdc": str(spent),
        "fees_usdc": str(fees),
        "stop_loss": ticket.stop_loss,
        "take_profit": ticket.take_profit,
        "order_id": order_id,
        "client_order_id": cid,
        "partial": state == "PARTIAL",
    }
    write_positions(store, positions)
    _set_outcome(store, cid, {"state": state, "order_id": order_id, "side": "BUY",
                              "value_usdc": str(spent), "fees_usdc": str(fees)})
    out["steps"]["review"] = {
        "requested_usdc": str(ticket.quote_size),
        "spent_usdc": str(spent),
        "within_capital": spent <= controller.limits.total_capital_usdc,
    }
    return f"{state}: {filled} {ticket.product_id.split('-')[0]} fuer {spent} USDC (inkl. Gebuehr)"


def close_position(
    symbol: str,
    *,
    controller: ModeController,
    connector: Any,
    store: SafetyStore,
    reason: str,
) -> dict:
    """Sell the recorded position and book the realised result, fees included.

    Exits reduce risk, so they need no capital approval - but they still need
    an armed autonomous mode and no emergency stop, and they are deduplicated
    like buys. With an emergency stop active the position stays open until a
    human decides; the stop blocks every order, exits included.
    """
    out = {"symbol": symbol, "reason": reason, "sent": False}
    pos = read_positions(store).get(symbol)
    if not pos:
        out["result"] = "Keine Position"
        return out
    if controller.emergency_stop:
        out["result"] = (
            f"BLOCKIERT: Not-Aus aktiv ({controller.stop_reason}) - Position bleibt offen"
        )
        return out
    if (
        controller.mode is not TradingMode.LIVE_AUTONOMOUS
        or not controller.autonomous_armed
    ):
        out["result"] = "BLOCKIERT: kein scharfgeschalteter autonomer Modus"
        return out
    base = pos["base_size"]
    cid = new_client_order_id("hg-x")
    if not store.claim_order_id(
        cid, {"product_id": symbol, "side": "SELL", "base_size": base}
    ):
        out["result"] = "BLOCKIERT: doppelte Order-ID"
        return out
    try:
        created = connector.execute_real_sell(
            symbol, base, cid, _phrase("SELL", symbol, base)
        )
        order_id = created["order_id"]
    except Exception as exc:  # noqa: BLE001
        controller.trigger_emergency_stop(
            f"Verkauf unklar ({type(exc).__name__})", source="pipeline"
        )
        out["result"] = "UNBEKANNT: Verkauf nicht bestaetigt - Not-Aus gesetzt"
        return out
    out["sent"] = True
    state = classify_fill(_read_order(connector, order_id), D(base))
    if state.state != "FILLED":
        controller.trigger_emergency_stop(
            f"Verkauf nicht vollstaendig ({state.state})", source="pipeline"
        )
        out["result"] = f"{state.state}: {state.action}"
        return out
    order = connector.get_real_order_status(order_id)
    proceeds = D(str(order.get("total_value_after_fees") or "0"))
    pnl = proceeds - D(str(pos["cost_usdc"]))  # both legs already net of fees
    positions = read_positions(store)
    positions.pop(symbol, None)
    write_positions(store, positions)
    _set_outcome(store, cid, {"state": "FILLED", "order_id": order_id, "side": "SELL",
                              "value_usdc": str(proceeds),
                              "fees_usdc": str(order.get("total_fees") or "0"),
                              "realised_pnl_usdc": str(pnl)})
    breach = controller.book_realised(pnl)
    out.update(
        {
            "realised_pnl_usdc": str(pnl),
            "loss_breach": breach,
            "result": f"GESCHLOSSEN: P&L {pnl} USDC",
        }
    )
    return out


def resolve_unresolved(store: SafetyStore, connector: Any) -> list:
    """After a restart: for every claimed order without an outcome, ask
    Coinbase by client order id. Never re-sends. Orders Coinbase does not know
    are marked NOT_SENT; anything else stays blocked for a human to settle."""
    report = []
    for cid in unresolved_orders(store):
        try:
            found = connector.find_order_by_client_id(cid)
        except Exception as exc:  # noqa: BLE001
            report.append(
                {
                    "client_order_id": cid,
                    "state": "UNKNOWN",
                    "error": type(exc).__name__,
                }
            )
            continue
        if found is None:
            _set_outcome(store, cid, {"state": "NOT_SENT"})
            report.append({"client_order_id": cid, "state": "NOT_SENT"})
        else:
            report.append(
                {
                    "client_order_id": cid,
                    "state": "NEEDS_REVIEW",
                    "order_id": found.get("order_id"),
                    "status": found.get("status"),
                }
            )
    return report
