"""LIVE_READINESS_CHECK (Phase 14).

Fourteen criteria, exactly the ones Nate listed. Each one is PASS only on
evidence; a criterion that cannot be checked is FAIL, never "assumed fine".

Two kinds of evidence are used:
  * self-tests - the safety mechanisms are exercised for real against a
    temporary directory (never the production ``state/``);
  * live evidence - facts read from the running system: the connector that
    holds the API key, the auth store, the age of the market data.

The verdict is READY only when all fourteen pass. Even then this module arms
nothing: it returns a report. Arming is a separate human step
(``ModeController.arm_autonomous``).
"""

from __future__ import annotations

import tempfile
import time
from dataclasses import dataclass, field
from decimal import Decimal as D
from pathlib import Path
from typing import Any, Optional

from . import risk_config as rc
from .collaboration import DebateRoom, Opinion
from .core import RiskManager
from .execution_guard import (
    MAX_MARKET_AGE_S,
    check_order,
    classify_fill,
    read_back_status,
)
from .live_pipeline import ticket_from_meeting, unresolved_orders
from .meeting import Decision, hold_meeting
from .modes import AUTONOMOUS_ACTIVATION_PHRASE, ModeController, ModeError, TradingMode
from .persistence import SafetyStore

READY = "READY FOR FINAL LIVE ACTIVATION APPROVAL"
NOT_READY = "NOT READY"


@dataclass
class Criterion:
    number: int
    key: str
    title: str
    passed: bool = False
    evidence: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "key": self.key,
            "title": self.title,
            "passed": self.passed,
            "evidence": list(self.evidence),
        }


def _uptrend(n: int = 60) -> list:
    return [D(str(100 + i * 0.5)) for i in range(n)]


def _agreeing_room() -> DebateRoom:
    """A debate room whose voices all say BUY - used only to drive the
    self-tests to the point where the RiskManager and the gate are reached."""

    def voice(name):
        return lambda report, closes: Opinion(name, "BUY", D("0.9"), "Selbsttest")

    return DebateRoom(voices=[voice("A"), voice("B"), voice("C")])


class _DeadConnector:
    def get_real_order_status(self, order_id):
        raise TimeoutError("Selbsttest: Coinbase antwortet nicht")


# ---- the fourteen checks ---------------------------------------------------


def _c1_risk_config(c: Criterion, controller: ModeController) -> None:
    lim, want = controller.limits, rc.NATE_CONFIRMED_LIMITS
    ok = True
    for name in (
        "total_capital_usdc",
        "max_daily_loss_usdc",
        "max_total_loss_usdc",
        "max_slippage_pct",
        "max_open_exposure_usdc",
    ):
        have, ceiling = getattr(lim, name), getattr(want, name)
        good = 0 < have <= ceiling
        ok &= good
        c.evidence.append(
            f"{name}: {have} (Obergrenze {ceiling}) {'ok' if good else 'FALSCH'}"
        )
    ok &= lim.confirmed
    raised = lim.tightened(total_capital_usdc="1000", max_slippage_pct="50")
    clamp = (
        raised.total_capital_usdc == lim.total_capital_usdc
        and raised.max_slippage_pct == lim.max_slippage_pct
    )
    c.evidence.append(f"Erhoehungsversuch wird gekappt: {clamp}")
    flags_off = not (
        rc.LEVERAGE_ENABLED
        or rc.MARGIN_ENABLED
        or rc.WITHDRAWALS_ENABLED
        or rc.TRANSFERS_ENABLED
    )
    c.evidence.append(f"Hebel/Margin/Auszahlung/Transfer deaktiviert: {flags_off}")
    spot = rc.MARKET == "SPOT" and all(
        p.endswith("-USDC") for p in controller.allowed_products
    )
    c.evidence.append(f"Nur Spot-Produkte in USDC: {spot}")
    if rc.NATE_PROFILE.permits_total_loss():
        c.evidence.append(
            "HINWEIS: Die Konfiguration erlaubt den Totalverlust der 17.10 USDC."
        )
    c.passed = ok and clamp and flags_off and spot


def _c2_connection(c: Criterion, connector: Any) -> None:
    if connector is None:
        c.evidence.append(
            "Kein Coinbase-Connector mit API-Schluessel in diesem Prozess."
        )
        return
    try:
        perms = connector.permissions
        usdc = D(str(connector.get_available_funds("USDC")))
        connector.get_open_orders()
    except Exception as exc:  # noqa: BLE001
        c.evidence.append(
            f"Coinbase-Abfrage fehlgeschlagen: {type(exc).__name__}: {exc}"
        )
        return
    c.evidence.append(
        f"can_view={perms.get('can_view')} can_trade={perms.get('can_trade')} "
        f"can_transfer={perms.get('can_transfer')}"
    )
    c.evidence.append(f"Verfuegbar: {usdc} USDC")
    c.passed = bool(
        perms.get("can_view")
        and perms.get("can_trade")
        and not perms.get("can_transfer")
    )


def _c3_isolation(
    c: Criterion, connector: Any, expected_portfolio: Optional[str]
) -> None:
    if connector is None:
        c.evidence.append("Ohne Connector nicht pruefbar.")
        return
    perms = connector.permissions
    portfolio = perms.get("portfolio_uuid")
    c.evidence.append(f"Portfolio des API-Schluessels: {portfolio}")
    c.evidence.append(
        f"Erwartetes Portfolio: {expected_portfolio or 'nicht angegeben'}"
    )
    no_transfer = not perms.get("can_transfer")
    c.evidence.append(f"Schluessel kann nicht transferieren: {no_transfer}")
    c.evidence.append(
        "Kapitaldeckel 17.10 USDC gilt unabhaengig vom Kontostand; "
        "Einzahlungen erhoehen ihn nicht."
    )
    c.passed = bool(
        portfolio
        and expected_portfolio
        and portfolio == expected_portfolio
        and no_transfer
    )


def _c4_emergency_stop(c: Criterion, controller: ModeController, tmp: Path) -> None:
    store = SafetyStore(tmp / "c4")
    first = ModeController(rc.NATE_CONFIRMED_LIMITS, store=store)
    first.trigger_emergency_stop("Selbsttest")
    reborn = ModeController(rc.NATE_CONFIRMED_LIMITS, store=SafetyStore(tmp / "c4"))
    survives = reborn.emergency_stop
    blocked = False
    try:
        reborn.set_mode(TradingMode.LIVE_MANUAL)
    except ModeError:
        blocked = True
    needs_reason = False
    try:
        reborn.clear_emergency_stop()
    except ModeError:
        needs_reason = True
    store.stop_path.write_text("{kaputt")
    fail_closed = SafetyStore(tmp / "c4").read_emergency_stop().active
    c.evidence += [
        f"Not-Aus ueberlebt Neustart: {survives}",
        f"Moduswechsel bei Not-Aus verweigert: {blocked}",
        f"Loeschen verlangt Person und Grund: {needs_reason}",
        f"Defekte Not-Aus-Datei gilt als STOP: {fail_closed}",
        f"Produktiver Controller ist persistent: {controller.persistent}",
    ]
    c.passed = (
        survives and blocked and needs_reason and fail_closed and controller.persistent
    )


def _c5_loss_ledger(c: Criterion, controller: ModeController, tmp: Path) -> None:
    store = SafetyStore(tmp / "c5")
    first = ModeController(rc.NATE_CONFIRMED_LIMITS, store=store)
    first.book_realised(D("-5.00"))
    reborn = ModeController(rc.NATE_CONFIRMED_LIMITS, store=SafetyStore(tmp / "c5"))
    kept = reborn.loss_state()["total_loss"] == D("5.00")
    breach = reborn.book_realised(D("-12.10"))
    stopped = reborn.emergency_stop
    c.evidence += [
        f"Verlust nach Neustart noch gebucht: {kept}",
        f"Grenze 17.10 erreicht -> Meldung: {bool(breach)}",
        f"Grenzverletzung loest persistenten Not-Aus aus: {stopped}",
        f"Produktiver Controller ist persistent: {controller.persistent}",
    ]
    c.passed = kept and bool(breach) and stopped and controller.persistent


def _c6_dedup(c: Criterion, tmp: Path) -> None:
    store = SafetyStore(tmp / "c6")
    first = store.claim_order_id("hg-selbsttest", {"side": "BUY"})
    second = SafetyStore(tmp / "c6").claim_order_id("hg-selbsttest", {"side": "BUY"})
    c.evidence += [
        f"Erste Reservierung angenommen: {first}",
        f"Zweite Reservierung (auch nach Neustart) abgelehnt: {not second}",
    ]
    c.passed = first and not second


def _c7_restart(c: Criterion, tmp: Path) -> None:
    store = SafetyStore(tmp / "c7")
    ctl = ModeController(rc.NATE_CONFIRMED_LIMITS, store=store)
    ctl.arm_autonomous(AUTONOMOUS_ACTIVATION_PHRASE, True, armed_by="Selbsttest")
    ctl.set_mode(TradingMode.LIVE_AUTONOMOUS)
    store.claim_order_id("hg-unterwegs", {"side": "BUY"})  # crash before outcome
    reborn = ModeController(rc.NATE_CONFIRMED_LIMITS, store=SafetyStore(tmp / "c7"))
    paper = reborn.mode is TradingMode.PAPER and not reborn.autonomous_armed
    pending = unresolved_orders(reborn.store) == ["hg-unterwegs"]
    c.evidence += [
        f"Nach Neustart PAPER und nicht scharf: {paper}",
        f"Unterwegs gewesene Order blockiert neue Orders: {pending}",
    ]
    c.passed = paper and pending


def _c8_api_errors(c: Criterion) -> None:
    state = read_back_status(
        _DeadConnector(), "x", D("1"), attempts=2, sleep=lambda s: None
    )
    unknown = state.state == "UNKNOWN" and state.blocks_new_orders
    none_is_unknown = classify_fill(None, D("1")).state == "UNKNOWN"
    ctl = ModeController(rc.NATE_CONFIRMED_LIMITS)
    gate = check_order(ctl, product_id="BTC-USDC", side="BUY", notional_usdc=D("5"))
    blocked = not gate.allowed and len(gate.reasons) >= 4
    c.evidence += [
        f"Timeout beim Statusabruf -> UNKNOWN, blockiert: {unknown}",
        f"Fehlender Status wird nie als 'nicht passiert' gewertet: {none_is_unknown}",
        f"Unbekannte Werte (Guthaben, Gebuehr, Marktalter) blockieren: {blocked}",
    ]
    c.passed = unknown and none_is_unknown and blocked


def _c9_meeting_required(c: Criterion) -> None:
    ctl = ModeController(rc.NATE_CONFIRMED_LIMITS)
    res = hold_meeting(
        "BTC-USDC",
        _uptrend(),
        risk=RiskManager(rc.live_risk_config()),
        controller=ctl,
        available_usdc=D("17.10"),
        room=_agreeing_room(),
    )
    good = ticket_from_meeting(res, ctl, D("17.10"))
    never_sends = res.executed is False
    res.statements = [s for s in res.statements if s.agent != "TradeReviewer"]
    incomplete = ticket_from_meeting(res, ctl, D("17.10"))
    c.evidence += [
        f"Vollstaendiges Meeting ergibt gueltiges Ticket: {good.ok}",
        f"Meeting selbst sendet nie: {never_sends}",
        f"Unvollstaendiges Protokoll wird abgelehnt: {not incomplete.ok}",
    ]
    c.passed = good.ok and never_sends and not incomplete.ok


def _c10_veto(c: Criterion) -> None:
    ctl = ModeController(rc.NATE_CONFIRMED_LIMITS)
    risk = RiskManager(rc.live_risk_config())
    risk.emergency_stop("Selbsttest-Veto")
    res = hold_meeting(
        "BTC-USDC",
        _uptrend(),
        risk=risk,
        controller=ctl,
        available_usdc=D("17.10"),
        room=_agreeing_room(),
    )
    veto = res.final is Decision.VETO and res.prepared_order is None
    refused = not ticket_from_meeting(res, ctl, D("17.10")).ok
    c.evidence += [
        f"Veto beendet das Meeting ohne Order: {veto}",
        f"Aus einem Veto-Protokoll entsteht kein Ticket: {refused}",
    ]
    c.passed = veto and refused


def _c11_auth(c: Criterion, auth_store: Any) -> None:
    if auth_store is None:
        c.evidence.append("Kein AuthStore uebergeben.")
        return
    admins = [u for u, r in auth_store.users.items() if r.get("role") == "admin"]
    hashed = all(
        "password" not in r and r.get("hash") for r in auth_store.users.values()
    )
    c.evidence += [
        f"Admin-Konten: {len(admins)}",
        f"Nur gehashte Passwoerter: {hashed}",
    ]
    c.passed = bool(admins) and hashed


def _c12_audit(c: Criterion, auth_store: Any, audit_file: Optional[Path]) -> None:
    if auth_store is None or audit_file is None:
        c.evidence.append("Audit-Log nicht uebergeben.")
        return
    before = audit_file.stat().st_size if audit_file.exists() else 0
    auth_store.audit("readiness_check")
    after = audit_file.stat().st_size if audit_file.exists() else 0
    c.evidence.append(f"Audit-Eintrag geschrieben ({before} -> {after} Bytes)")
    c.passed = after > before


def _c13_market(c: Criterion, market_updated_at: Optional[float], now: float) -> None:
    if market_updated_at is None:
        c.evidence.append("Keine Marktdaten geladen.")
        return
    age = now - market_updated_at
    c.evidence.append(f"Alter der Marktdaten: {age:.0f}s (Grenze {MAX_MARKET_AGE_S}s)")
    c.passed = age <= MAX_MARKET_AGE_S


def _c14_reconciliation(
    c: Criterion, connector: Any, known_orders: Optional[dict]
) -> None:
    logic = (
        classify_fill({"status": "FILLED", "filled_size": "1"}, D("1")).state
        == "FILLED"
        and classify_fill({"status": "CANCELLED", "filled_size": "0.4"}, D("1")).state
        == "PARTIAL"
        and classify_fill({"status": "OPEN", "filled_size": "0"}, D("1")).state
        == "OPEN"
    )
    c.evidence.append(f"Klassifizierung FILLED/PARTIAL/OPEN korrekt: {logic}")
    if connector is None or not known_orders:
        c.evidence.append("Kein Live-Abgleich: Connector oder Referenzorders fehlen.")
        return
    live = True
    for order_id, want in known_orders.items():
        try:
            got = connector.get_real_order_status(order_id)
        except Exception as exc:  # noqa: BLE001
            c.evidence.append(f"{order_id}: nicht lesbar ({type(exc).__name__})")
            live = False
            continue
        same = (
            got.get("status") == "FILLED"
            and D(str(got.get("filled_size"))) == D(str(want["filled_size"]))
            and got.get("side") == want["side"]
        )
        c.evidence.append(
            f"{order_id}: {got.get('side')} {got.get('filled_size')} "
            f"{got.get('status')} {'ok' if same else 'ABWEICHUNG'}"
        )
        live &= same
    c.passed = logic and live


TITLES = [
    ("risk_config", "Korrekte Risikokonfiguration"),
    ("coinbase_connection", "Coinbase-Verbindung"),
    ("portfolio_isolation", "Portfolio-Isolation"),
    ("emergency_stop", "Funktionsfaehiger Not-Aus"),
    ("persistent_loss", "Persistente Verlustberechnung"),
    ("order_dedup", "Order-Deduplizierung"),
    ("restart_safety", "Neustartsicherheit"),
    ("api_error_handling", "API-Fehlerbehandlung"),
    ("meeting_required", "Team-Meeting-Pflicht"),
    ("risk_veto", "RiskManager-Veto"),
    ("authentication", "Authentifizierung"),
    ("audit_logging", "Audit-Logging"),
    ("market_data", "Aktuelle Marktdaten"),
    ("order_reconciliation", "Order-Reconciliation"),
]

#: The two real BTC-USDC orders from 2026-11-13, used as reconciliation anchors.
KNOWN_ORDERS = {
    "66b81bf7-fe78-4f48-9d0e-32b015e2ab8c": {
        "side": "BUY",
        "filled_size": "0.00016017",
    },
    "fcda9f60-6378-4c73-a118-467acee76271": {
        "side": "SELL",
        "filled_size": "0.00016017",
    },
}


def run_readiness_check(
    *,
    controller: ModeController,
    connector: Any = None,
    auth_store: Any = None,
    audit_file: Optional[Path] = None,
    market_updated_at: Optional[float] = None,
    expected_portfolio_id: Optional[str] = None,
    known_orders: Optional[dict] = None,
    now: Optional[float] = None,
) -> dict:
    now = time.time() if now is None else now
    cs = [Criterion(i + 1, key, title) for i, (key, title) in enumerate(TITLES)]
    with tempfile.TemporaryDirectory(prefix="hg-readiness-") as tmp_name:
        tmp = Path(tmp_name)
        steps = [
            lambda: _c1_risk_config(cs[0], controller),
            lambda: _c2_connection(cs[1], connector),
            lambda: _c3_isolation(cs[2], connector, expected_portfolio_id),
            lambda: _c4_emergency_stop(cs[3], controller, tmp),
            lambda: _c5_loss_ledger(cs[4], controller, tmp),
            lambda: _c6_dedup(cs[5], tmp),
            lambda: _c7_restart(cs[6], tmp),
            lambda: _c8_api_errors(cs[7]),
            lambda: _c9_meeting_required(cs[8]),
            lambda: _c10_veto(cs[9]),
            lambda: _c11_auth(cs[10], auth_store),
            lambda: _c12_audit(cs[11], auth_store, audit_file),
            lambda: _c13_market(cs[12], market_updated_at, now),
            lambda: _c14_reconciliation(cs[13], connector, known_orders),
        ]
        for criterion, step in zip(cs, steps):
            try:
                step()
            except (
                Exception
            ) as exc:  # noqa: BLE001 - a crashing check is a failed check
                criterion.passed = False
                criterion.evidence.append(
                    f"Pruefung abgebrochen: {type(exc).__name__}: {exc}"
                )
    passed = sum(1 for c in cs if c.passed)
    all_ok = passed == len(cs)
    return {
        "verdict": READY if all_ok else NOT_READY,
        "passed": passed,
        "total": len(cs),
        "checked_at": now,
        "live_autonomous_enabled": controller.autonomous_armed,
        "mode": controller.mode.value,
        "emergency_stop": controller.emergency_stop,
        "risk_profile": rc.NATE_PROFILE.to_dict(),
        "criteria": [c.to_dict() for c in cs],
        "failed": [c.title for c in cs if not c.passed],
        "note": (
            "Dieser Bericht schaltet nichts scharf. Die Aktivierung ist ein "
            "eigener, ausdruecklicher Schritt von Nate."
        ),
    }
