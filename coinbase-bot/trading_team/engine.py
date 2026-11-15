"""Strategy championship, the runner, and continuous position monitoring
(Phase 15/16). This is NOT a second trading engine: every order still goes
through the one meeting, the one RiskManager veto and the one execution path in
``meeting.py`` / ``live_pipeline.py``. This module only decides *which* candidate
to bring to that meeting, runs it on a schedule, and watches open positions.

Separation of money:
  * LIVE orders and the real loss ledger live in ``state/positions.json`` and
    ``state/loss_ledger.json`` and are booked only by ``live_pipeline``.
  * PAPER orders live in ``state/paper_positions.json`` /
    ``state/paper_ledger.json`` and never touch the real ledger. Forward paper
    trading uses real Coinbase market data but books nothing real.

The emergency stop blocks new entries in every mode; risk-reducing exits still
run (``live_pipeline.close_position`` for real, ``paper_close`` for paper).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal as D
from pathlib import Path
from typing import Any, Optional

from .live_pipeline import (
    close_position,
    log_meeting,
    read_positions,
    run_cycle,
    ticket_from_meeting,
    unresolved_orders,
)
from .meeting import hold_meeting
from .modes import ModeController, TradingMode
from .persistence import SafetyStore, _atomic_write_json, _read_json
from .strategies import ALL_STRATEGIES


def _utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---- strategy championship -------------------------------------------------


@dataclass
class StrategyVerdict:
    name: str
    side: str  # BUY | SELL | HOLD
    agree: int  # how many strategies share this non-HOLD side
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "side": self.side,
            "agree": self.agree,
            "note": self.note,
        }


def run_championship(bars: list, *, quorum: int = 3) -> dict:
    """Run every strategy on the SAME bars and let them compete. The winner is
    the side with the most votes, but only when it reaches the quorum and beats
    the opposite side - otherwise the verdict is HOLD. One shared winner is
    carried to the meeting; the strategies never each spend the budget.

    Only long entries are proposed here (spot, no shorting); a SELL majority
    means 'do not enter', exits are the monitor's job.
    """
    votes = {}
    for name, fn in ALL_STRATEGIES.items():
        try:
            votes[name] = fn(bars)
        except Exception:  # noqa: BLE001
            votes[name] = "HOLD"
    buys = [n for n, s in votes.items() if s == "BUY"]
    sells = [n for n, s in votes.items() if s == "SELL"]
    if len(buys) >= quorum and len(buys) > len(sells):
        winner = "BUY"
    elif len(sells) >= quorum and len(sells) > len(buys):
        winner = "SELL"
    else:
        winner = "HOLD"
    ranked = sorted(
        (
            StrategyVerdict(
                n, s, len(buys) if s == "BUY" else len(sells) if s == "SELL" else 0
            )
            for n, s in votes.items()
        ),
        key=lambda v: (-v.agree, v.name),
    )
    return {
        "winner_side": winner,
        "buy_votes": len(buys),
        "sell_votes": len(sells),
        "quorum": quorum,
        "ranked": [v.to_dict() for v in ranked],
        "note": (
            f"{len(buys)} BUY / {len(sells)} SELL von {len(votes)} Strategien; "
            f"Sieger {winner}"
        ),
    }


# ---- paper book (separate from real money) ---------------------------------


def _paper_positions_path(store: SafetyStore) -> Path:
    return store.dir / "paper_positions.json"


def _paper_ledger_path(store: SafetyStore) -> Path:
    return store.dir / "paper_ledger.json"


def read_paper_positions(store: SafetyStore) -> dict:
    return dict(_read_json(_paper_positions_path(store)))


def read_paper_ledger(store: SafetyStore) -> dict:
    data = _read_json(_paper_ledger_path(store))
    return {
        "total_realised": D(str(data.get("total_realised", "0"))),
        "per_day": dict(data.get("per_day") or {}),
    }


def _book_paper(store: SafetyStore, pnl: D) -> None:
    ledger = read_paper_ledger(store)
    day = _utc_day()
    ledger["per_day"][day] = str(D(str(ledger["per_day"].get(day, "0"))) + pnl)
    ledger["total_realised"] = ledger["total_realised"] + pnl
    _atomic_write_json(
        _paper_ledger_path(store),
        {"total_realised": str(ledger["total_realised"]), "per_day": ledger["per_day"]},
    )


def paper_buy(
    symbol: str,
    quote_usdc: D,
    price: D,
    *,
    store: SafetyStore,
    fee_rate: D,
    stop_loss: str = "",
    take_profit: str = "",
    now: Optional[float] = None,
) -> dict:
    """Simulate a market buy at ``price`` with the real taker fee. Books a
    paper position only; no order is sent anywhere."""
    quote = D(str(quote_usdc))
    fee = (quote * D(str(fee_rate))).quantize(D("0.000001"))
    base = ((quote - fee) / D(str(price))).quantize(
        D("0.00000001"), rounding=ROUND_DOWN
    )
    positions = read_paper_positions(store)
    positions[symbol] = {
        "base_size": str(base),
        "cost_usdc": str(quote),
        "entry_price": str(price),
        "fees_usdc": str(fee),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "opened_at": time.time() if now is None else now,
    }
    _atomic_write_json(_paper_positions_path(store), positions)
    return positions[symbol]


def paper_close(
    symbol: str, price: D, *, store: SafetyStore, fee_rate: D, reason: str
) -> dict:
    positions = read_paper_positions(store)
    pos = positions.get(symbol)
    if not pos:
        return {"symbol": symbol, "result": "Keine Paper-Position"}
    proceeds = D(str(pos["base_size"])) * D(str(price))
    fee = (proceeds * D(str(fee_rate))).quantize(D("0.000001"))
    net = proceeds - fee
    pnl = (net - D(str(pos["cost_usdc"]))).quantize(D("0.000001"))
    positions.pop(symbol, None)
    _atomic_write_json(_paper_positions_path(store), positions)
    _book_paper(store, pnl)
    return {
        "symbol": symbol,
        "reason": reason,
        "exit_price": str(price),
        "realised_pnl_usdc": str(pnl),
        "result": f"PAPER GESCHLOSSEN: {pnl} USDC",
    }


# ---- the runner ------------------------------------------------------------


def _slippage_from_quote(quote: dict, side: str) -> Optional[D]:
    try:
        bid, ask = D(str(quote["bid"])), D(str(quote["ask"]))
    except Exception:  # noqa: BLE001
        return None
    if bid <= 0 or ask <= 0:
        return None
    mid = (bid + ask) / 2
    edge = ask if side == "BUY" else bid
    return abs(edge - mid) / mid * 100


def run_once(
    symbol: str,
    ohlcv: list,
    *,
    controller: ModeController,
    risk,
    connector: Any,
    store: SafetyStore,
    market_updated_at: Optional[float],
    fee_rate: D,
    min_order_usdc: D,
    mode: Optional[TradingMode] = None,
    approval: Optional[str] = None,
    now: Optional[float] = None,
) -> dict:
    """One tick for one product. ``ohlcv`` is a list of completed OHLCV bars
    (dicts with o,h,l,c,v); the championship reads them, the meeting reads the
    closes derived from them. Only a BUY winner reaches the full meeting; then
    execution is routed by mode: PAPER simulates, LIVE_MANUAL / LIVE_AUTONOMOUS
    go through the real ``run_cycle``. The record is appended to the meeting log.
    """
    mode = mode or controller.mode
    bars = [D(str(b["c"])) for b in ohlcv]   # closes for meeting + sizing
    out: dict = {
        "symbol": symbol,
        "ts": time.time() if now is None else now,
        "mode": mode.value,
        "sent": False,
        "steps": {},
    }

    def finish(note: str) -> dict:
        out["result"] = note
        log_meeting(store, out)
        return out

    pending = unresolved_orders(store)
    if pending:
        return finish(f"BLOCKIERT: ungeklaerte Order(s) {pending}")

    champ = run_championship(ohlcv)
    out["championship"] = champ
    if champ["winner_side"] != "BUY":
        return finish(f"NO TRADE: Championship {champ['note']}")
    if symbol in read_positions(store) or symbol in read_paper_positions(store):
        return finish("NO TRADE: Position besteht bereits")

    # LIVE entries go through the existing real path, unchanged.
    if mode in (TradingMode.LIVE_MANUAL, TradingMode.LIVE_AUTONOMOUS):
        live = run_cycle(
            symbol,
            bars,
            controller=controller,
            risk=risk,
            connector=connector,
            store=store,
            market_updated_at=market_updated_at,
            fee_rate=fee_rate,
            min_order_usdc=min_order_usdc,
            approval=approval,
            now=now,
        )
        out.update(
            {k: live[k] for k in ("sent", "steps", "result", "meeting") if k in live}
        )
        return out

    # PAPER: same meeting and the same entry risk rules, simulated fill.
    if controller.emergency_stop:
        return finish(f"BLOCKIERT: Not-Aus aktiv ({controller.stop_reason})")
    try:
        available = D(str(connector.get_available_funds("USDC")))
        quote = connector.get_market_price(symbol)
    except Exception as exc:  # noqa: BLE001
        return finish(
            f"BLOCKIERT: Marktdaten/Guthaben nicht lesbar ({type(exc).__name__})"
        )
    paper_exposure = sum(
        (D(str(p["cost_usdc"])) for p in read_paper_positions(store).values()), D("0")
    )
    meeting = hold_meeting(
        symbol,
        bars,
        risk=risk,
        controller=controller,
        available_usdc=available,
        open_exposure_usdc=paper_exposure,
        fee_rate=fee_rate,
        min_order_usdc=min_order_usdc,
    )
    out["meeting"] = meeting.to_dict()
    ticket = ticket_from_meeting(meeting, controller, available, paper_exposure)
    out["steps"]["ticket"] = {"ok": ticket.ok, "reasons": ticket.reasons}
    if not ticket.ok or ticket.side != "BUY":
        return finish("NO TRADE: " + "; ".join(ticket.reasons or ["kein BUY"]))

    slippage = _slippage_from_quote(quote, "BUY")
    reasons = controller.risk_reasons(
        "BUY",
        symbol,
        expected_slippage_pct=slippage,
        notional_usdc=ticket.quote_size,
        open_exposure_usdc=paper_exposure,
    )
    stale = market_updated_at is None or (out["ts"] - market_updated_at) > 90
    if stale:
        reasons.append("Marktdaten veraltet")
    if slippage is None:
        reasons.append("Slippage unbekannt")
    out["steps"]["risk"] = {
        "slippage_pct": None if slippage is None else str(slippage),
        "reasons": reasons,
    }
    if reasons:
        return finish("NO TRADE (Paper-Risk): " + "; ".join(reasons))

    price = D(str(quote["ask"]))
    pos = paper_buy(
        symbol,
        ticket.quote_size,
        price,
        store=store,
        fee_rate=fee_rate,
        stop_loss=ticket.stop_loss,
        take_profit=ticket.take_profit,
        now=out["ts"],
    )
    out["sent"] = True
    out["steps"]["paper_fill"] = pos
    return finish(
        f"PAPER BUY: {pos['base_size']} {symbol.split('-')[0]} "
        f"zu {price} (Einsatz {ticket.quote_size} USDC)"
    )


# ---- continuous position monitoring ---------------------------------------


@dataclass
class ExitRule:
    """How open positions are watched. Stop-loss and take-profit come from the
    meeting; the time exit is a hard cap on how long a position may stay open."""

    max_hold_seconds: float = 86400.0  # one day
    use_position_levels: bool = True  # honour per-position stop/take


def _decide_exit(pos: dict, price: D, now: float, rule: ExitRule) -> Optional[str]:
    opened = float(pos.get("opened_at") or 0)
    if rule.use_position_levels:
        stop = pos.get("stop_loss")
        take = pos.get("take_profit")
        if stop and D(str(stop)) > 0 and price <= D(str(stop)):
            return f"Stop-Loss ({price} <= {stop})"
        if take and D(str(take)) > 0 and price >= D(str(take)):
            return f"Take-Profit ({price} >= {take})"
    if opened and (now - opened) >= rule.max_hold_seconds:
        return f"Zeit-Exit (gehalten {int(now - opened)}s)"
    return None


def monitor_positions(
    prices: dict,
    *,
    controller: ModeController,
    connector: Any,
    store: SafetyStore,
    rule: Optional[ExitRule] = None,
    paper: bool = False,
    fee_rate: D = D("0.001"),
    market_stale: bool = False,
    now: Optional[float] = None,
) -> dict:
    """Check every open position once and act on stop-loss / take-profit / time.

    A position whose price is unknown or stale cannot be acted on - we never
    invent a price - so it is reported as ``watch_blocked`` and left open, and
    the caller keeps checking. Real exits run even under the emergency stop
    (risk reduction); paper exits use the paper book.
    """
    rule = rule or ExitRule()
    now = time.time() if now is None else now
    positions = read_paper_positions(store) if paper else read_positions(store)
    actions, blocked = [], []
    for symbol, pos in positions.items():
        feed = prices.get(symbol) or prices.get(symbol.replace("-USDC", "-USD"))
        price = (
            None
            if (feed is None or market_stale)
            else D(str(feed["price"] if isinstance(feed, dict) else feed))
        )
        if price is None:
            blocked.append(
                {"symbol": symbol, "reason": "Preis unbekannt/veraltet - Exit wartet"}
            )
            continue
        why = _decide_exit(pos, price, now, rule)
        if not why:
            continue
        if paper:
            actions.append(
                paper_close(symbol, price, store=store, fee_rate=fee_rate, reason=why)
            )
        else:
            actions.append(
                close_position(
                    symbol,
                    controller=controller,
                    connector=connector,
                    store=store,
                    reason=why,
                )
            )
    return {
        "checked": len(positions),
        "actions": actions,
        "watch_blocked": blocked,
        "market_stale": market_stale,
    }
