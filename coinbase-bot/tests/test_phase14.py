"""Phase 14: live-readiness safety tests. No test here talks to Coinbase; the
connector is a fake that records every call so 'nothing was sent' is provable."""

import time
from decimal import Decimal as D

import pytest

import trading_team.live_pipeline as pipeline
from trading_team.collaboration import DebateRoom, Opinion
from trading_team.core import RiskManager
from trading_team.execution_guard import check_order, classify_fill, realised_pnl
from trading_team.live_pipeline import (
    close_position,
    read_positions,
    resolve_unresolved,
    run_cycle,
    ticket_from_meeting,
    unresolved_orders,
)
from trading_team.meeting import Decision, hold_meeting
from trading_team.modes import (
    AUTONOMOUS_ACTIVATION_PHRASE,
    ModeController,
    ModeError,
    TradingMode,
)
from trading_team.persistence import SafetyStore
from trading_team.readiness import KNOWN_ORDERS, NOT_READY, READY, run_readiness_check
from trading_team.risk_config import (
    LIVE_AUTONOMOUS_ENABLED,
    NATE_CONFIRMED_LIMITS,
    NATE_PROFILE,
    live_risk_config,
)

PORTFOLIO = "pf-test"


def uptrend(n=60):
    return [D(str(100 + i * 0.5)) for i in range(n)]


def buy_room():
    def voice(name):
        return lambda report, closes: Opinion(name, "BUY", D("0.9"), "Test")

    return DebateRoom(voices=[voice("A"), voice("B"), voice("C")])


class FakeConnector:
    """Stands in for CoinbaseLiveConnector. Counts every order sent."""

    sell_proceeds = D("0")

    def __init__(self, usdc="17.10", fill="full", send_error=None, status_error=False):
        self.usdc, self.fill = D(usdc), fill
        self.send_error, self.status_error = send_error, status_error
        self.buys, self.sells, self.orders = [], [], {}
        self.permissions = {
            "can_view": True,
            "can_trade": True,
            "can_transfer": False,
            "portfolio_uuid": PORTFOLIO,
        }
        self.bid, self.ask = D("129.45"), D("129.55")

    def get_available_funds(self, currency):
        return self.usdc

    def get_open_orders(self):
        return []

    def get_market_price(self, product_id):
        return {"bid": self.bid, "ask": self.ask}

    def preview_buy_order(self, product_id, quote_size):
        return {"quote_size": quote_size, "commission_total": "0.01"}

    def execute_real_buy(self, product_id, quote_size, client_order_id, confirmation):
        assert confirmation == f"EXECUTE BUY {product_id} {quote_size}"
        self.buys.append((product_id, quote_size, client_order_id))
        if self.send_error:
            raise self.send_error
        oid = f"o-{len(self.buys)}"
        quote = D(quote_size)
        part = D("1") if self.fill == "full" else D("0.4")
        self.orders[oid] = {
            "order_id": oid,
            "client_order_id": client_order_id,
            "side": "BUY",
            "status": "FILLED" if self.fill == "full" else "CANCELLED",
            "filled_size": str((quote * part / self.ask).quantize(D("0.00000001"))),
            "total_value_after_fees": str(quote * part),
            "total_fees": str(quote * part * D("0.001")),
        }
        return {"order_id": oid}

    def execute_real_sell(self, product_id, base_size, client_order_id, confirmation):
        self.sells.append((product_id, base_size, client_order_id))
        oid = f"s-{len(self.sells)}"
        self.orders[oid] = {
            "order_id": oid,
            "client_order_id": client_order_id,
            "side": "SELL",
            "status": "FILLED",
            "filled_size": base_size,
            "total_value_after_fees": str(self.sell_proceeds),
            "total_fees": "0.01",
        }
        return {"order_id": oid}

    def get_real_order_status(self, order_id):
        if self.status_error:
            raise TimeoutError("kein Status")
        return self.orders[order_id]

    def find_order_by_client_id(self, cid):
        return next(
            (o for o in self.orders.values() if o["client_order_id"] == cid), None
        )


def armed(tmp_path, name="s"):
    store = SafetyStore(tmp_path / name)
    ctl = ModeController(NATE_CONFIRMED_LIMITS, store=store)
    ctl.arm_autonomous(AUTONOMOUS_ACTIVATION_PHRASE, True, armed_by="pytest")
    ctl.set_mode(TradingMode.LIVE_AUTONOMOUS)
    return ctl, store


def cycle(ctl, store, conn, monkeypatch, **kw):
    monkeypatch.setattr(
        pipeline, "hold_meeting", lambda *a, **k: hold_meeting(*a, room=buy_room(), **k)
    )
    args = dict(
        controller=ctl,
        risk=RiskManager(live_risk_config()),
        connector=conn,
        store=store,
        market_updated_at=time.time(),
        fee_rate=D("0.001"),
        min_order_usdc=D("1"),
    )
    args.update(kw)
    return run_cycle("BTC-USDC", uptrend(), **args)


# ---- configuration ---------------------------------------------------------


def test_confirmed_values_are_exactly_nates():
    lim = NATE_CONFIRMED_LIMITS
    assert (
        lim.total_capital_usdc,
        lim.max_daily_loss_usdc,
        lim.max_total_loss_usdc,
        lim.max_slippage_pct,
    ) == (D("17.10"), D("17.10"), D("17.10"), D("2.0"))
    assert lim.confirmed and LIVE_AUTONOMOUS_ENABLED is False
    assert NATE_PROFILE.permits_total_loss()  # stated openly, not hidden


def test_risk_manager_can_tighten_but_never_raise():
    ctl = ModeController(NATE_CONFIRMED_LIMITS)
    ctl.tighten(
        "RiskManager",
        max_daily_loss_usdc="3",
        max_slippage_pct="50",
        total_capital_usdc="1000",
    )
    assert ctl.limits.max_daily_loss_usdc == D("3")
    assert ctl.limits.max_slippage_pct == D("2.0")
    assert ctl.limits.total_capital_usdc == D("17.10")
    assert [e["clamped"] for e in ctl.tighten_log] == [False, True, True]


def test_autonomous_stays_locked_without_every_condition(tmp_path):
    store = SafetyStore(tmp_path)
    ctl = ModeController(NATE_CONFIRMED_LIMITS, store=store)
    with pytest.raises(ModeError):
        ctl.set_mode(TradingMode.LIVE_AUTONOMOUS)
    for phrase, ready, who in [
        ("ja", True, "Nate"),
        (AUTONOMOUS_ACTIVATION_PHRASE, False, "Nate"),
        (AUTONOMOUS_ACTIVATION_PHRASE, True, ""),
    ]:
        with pytest.raises(ModeError):
            ctl.arm_autonomous(phrase, ready, armed_by=who)
    with pytest.raises(ModeError):  # no persistent store -> never
        ModeController(NATE_CONFIRMED_LIMITS).arm_autonomous(
            AUTONOMOUS_ACTIVATION_PHRASE, True, armed_by="Nate"
        )
    assert not ctl.autonomous_armed


def test_paper_mode_never_sends(tmp_path, monkeypatch):
    store = SafetyStore(tmp_path)
    ctl = ModeController(NATE_CONFIRMED_LIMITS, store=store)
    conn = FakeConnector()
    out = cycle(ctl, store, conn, monkeypatch)
    assert conn.buys == [] and out["sent"] is False and "PAPER" in out["result"]


def test_happy_path_books_position_with_fees(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector()
    out = cycle(ctl, store, conn, monkeypatch)
    assert out["sent"] and len(conn.buys) == 1, out["result"]
    pos = read_positions(store)["BTC-USDC"]
    assert D(pos["cost_usdc"]) <= D("17.10") and D(pos["fees_usdc"]) > 0
    assert unresolved_orders(store) == []
    again = cycle(ctl, store, conn, monkeypatch)  # already holding
    assert len(conn.buys) == 1 and again["sent"] is False


# ---- the ten scenarios -----------------------------------------------------


def test_s01_total_capital_loss_stops_everything_for_good(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector()
    cycle(ctl, store, conn, monkeypatch)
    conn.sell_proceeds = D("0")  # position became worthless
    out = close_position(
        "BTC-USDC", controller=ctl, connector=conn, store=store, reason="test"
    )
    assert D(out["realised_pnl_usdc"]) < 0
    ctl.book_realised(
        -(D("17.10") + D(out["realised_pnl_usdc"]))
    )  # up to the full 17.10
    assert ctl.emergency_stop and ctl.mode is TradingMode.PAPER
    reborn = ModeController(NATE_CONFIRMED_LIMITS, store=SafetyStore(tmp_path / "s"))
    assert reborn.emergency_stop  # a new session cannot bypass it
    with pytest.raises(ModeError):
        reborn.arm_autonomous(AUTONOMOUS_ACTIVATION_PHRASE, True, armed_by="Nate")
    assert cycle(reborn, reborn.store, conn, monkeypatch)["sent"] is False
    assert len(conn.buys) == 1


def test_s02_daily_loss_limit(tmp_path):
    store = SafetyStore(tmp_path)
    ctl = ModeController(
        NATE_CONFIRMED_LIMITS.tightened(max_daily_loss_usdc="2"), store=store
    )
    assert ctl.book_realised(D("-1.50")) is None
    assert "Tagesverlust" in ctl.book_realised(D("-0.60"))
    assert ctl.emergency_stop
    ok, reason = ctl.may_execute_live("BUY", "BTC-USDC", "5", None)
    assert not ok and "Not-Aus" in reason


def test_s03_total_loss_limit_counts_across_days_and_restarts(tmp_path):
    store = SafetyStore(tmp_path)
    store.book_realised(D("-9"), day="2026-11-10")
    store.book_realised(D("-8.10"), day="2026-11-11")
    ctl = ModeController(NATE_CONFIRMED_LIMITS, store=SafetyStore(tmp_path))
    assert ctl.loss_state()["daily_loss"] == 0  # nothing lost today
    assert "Gesamtverlust" in ctl.loss_breach()
    with pytest.raises(ModeError):
        ctl.arm_autonomous(AUTONOMOUS_ACTIVATION_PHRASE, True, armed_by="Nate")
    with pytest.raises(ModeError):
        ctl.set_mode(TradingMode.LIVE_AUTONOMOUS)
    ctl.mode = TradingMode.LIVE_MANUAL  # even forced past set_mode
    ok, reason = ctl.may_execute_live("BUY", "BTC-USDC", "5", "LIVE BUY BTC-USDC 5")
    assert not ok and "Verlustgrenze" in reason


def test_s04_slippage_above_two_percent_blocks(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector()
    conn.bid, conn.ask = D("120"), D("130")  # 4 % from mid
    out = cycle(ctl, store, conn, monkeypatch)
    assert conn.buys == [] and "Slippage" in out["result"]
    conn.bid = conn.ask = D("0")  # unknown slippage is not a pass
    assert "Slippage unbekannt" in cycle(ctl, store, conn, monkeypatch)["result"]
    assert conn.buys == []


def test_s05_coinbase_timeout_never_rebuys(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector(send_error=TimeoutError("read timed out"))
    out = cycle(ctl, store, conn, monkeypatch)
    assert len(conn.buys) == 1 and "UNBEKANNT" in out["result"]
    assert ctl.emergency_stop and len(unresolved_orders(store)) == 1
    conn.send_error = None
    for _ in range(3):  # retries must not send
        cycle(ctl, store, conn, monkeypatch)
    assert len(conn.buys) == 1


def test_s06_partial_fill_is_booked_at_filled_amount_only(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector(fill="partial")
    out = cycle(ctl, store, conn, monkeypatch)
    pos = read_positions(store)["BTC-USDC"]
    assert out["steps"]["fill"]["state"] == "PARTIAL" and pos["partial"] is True
    assert D(pos["cost_usdc"]) < D(out["steps"]["review"]["requested_usdc"])
    cycle(ctl, store, conn, monkeypatch)  # no automatic top-up
    assert len(conn.buys) == 1
    assert classify_fill(
        {"status": "OPEN", "filled_size": "0.4"}, D("1")
    ).blocks_new_orders


def test_s07_duplicate_buy_request(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    assert store.claim_order_id("hg-1", {"side": "BUY"})
    assert not store.claim_order_id("hg-1", {"side": "BUY"})
    assert not SafetyStore(tmp_path / "s").claim_order_id("hg-1", {"side": "BUY"})
    pipeline._set_outcome(store, "hg-1", {"state": "NOT_SENT"})
    conn = FakeConnector()
    cycle(ctl, store, conn, monkeypatch)
    cycle(ctl, store, conn, monkeypatch)  # same signal again
    assert len(conn.buys) == 1


def test_s08_backend_restart_during_an_order(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector(status_error=True)  # sent, then the process "dies"
    out = cycle(ctl, store, conn, monkeypatch)
    assert out["sent"] and "UNBEKANNT" in out["result"]
    store2 = SafetyStore(tmp_path / "s")
    reborn = ModeController(NATE_CONFIRMED_LIMITS, store=store2)
    assert reborn.mode is TradingMode.PAPER and not reborn.autonomous_armed
    assert reborn.emergency_stop and len(unresolved_orders(store2)) == 1
    conn.status_error = False
    assert cycle(reborn, store2, conn, monkeypatch)["sent"] is False
    report = resolve_unresolved(store2, conn)  # ask Coinbase, do not re-send
    assert report[0]["state"] == "NEEDS_REVIEW" and len(conn.buys) == 1


def test_s09_manipulated_agent_decision_is_refused():
    ctl = ModeController(NATE_CONFIRMED_LIMITS)

    def meeting():
        return hold_meeting(
            "BTC-USDC",
            uptrend(),
            risk=RiskManager(live_risk_config()),
            controller=ctl,
            available_usdc=D("17.10"),
            room=buy_room(),
        )

    assert ticket_from_meeting(meeting(), ctl, D("17.10")).ok
    bigger = meeting()
    bigger.prepared_order["quote_size"] = "500"
    other = meeting()
    other.prepared_order["product_id"] = "DOGE-USDC"
    flipped = meeting()
    flipped.prepared_order["side"] = "SELL"
    forged = meeting()
    forged.agreed = False
    risk = RiskManager(live_risk_config())
    risk.emergency_stop("x")
    vetoed = hold_meeting(
        "BTC-USDC",
        uptrend(),
        risk=risk,
        controller=ctl,
        available_usdc=D("17.10"),
        room=buy_room(),
    )
    vetoed.final = Decision.BUY  # someone overwrites the verdict
    vetoed.prepared_order = meeting().prepared_order
    for bad in (bigger, other, flipped, forged, vetoed):
        assert not ticket_from_meeting(bad, ctl, D("17.10")).ok
    manual = ModeController(NATE_CONFIRMED_LIMITS, mode=TradingMode.LIVE_MANUAL)
    ok, reason = manual.may_execute_live(
        "BUY", "DOGE-USDC", "5", "LIVE BUY DOGE-USDC 5"
    )
    assert not ok and "Freigabeliste" in reason


def test_s10_risk_manager_veto_is_binding(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    risk = RiskManager(live_risk_config())
    risk.emergency_stop("RiskManager sagt nein")
    conn = FakeConnector()
    out = cycle(ctl, store, conn, monkeypatch, risk=risk)
    assert (
        out["meeting"]["final"] == "VETO" and conn.buys == [] and out["sent"] is False
    )


# ---- remaining gates -------------------------------------------------------


def test_unknowns_block_new_orders(tmp_path):
    ctl, _ = armed(tmp_path)
    base = dict(
        product_id="BTC-USDC",
        side="BUY",
        notional_usdc=D("5"),
        available_usdc=D("17"),
        market_updated_at=1000.0,
        now=1010.0,
        fee_rate=D("0.001"),
        min_order_usdc=D("1"),
        expected_slippage_pct=D("0.1"),
    )
    assert check_order(ctl, **base).allowed
    for change, word in [
        ({"available_usdc": None}, "Guthaben"),
        ({"fee_rate": None}, "Gebuehr"),
        ({"min_order_usdc": None}, "Mindest"),
        ({"now": 2000.0}, "veraltet"),
        ({"market_updated_at": None}, "Marktdaten"),
        ({"available_usdc": D("3")}, "reicht nicht"),
        ({"expected_slippage_pct": None}, "Slippage unbekannt"),
        ({"open_orders": [{"product_id": "BTC-USDC"}]}, "Offene Order"),
        ({"open_exposure_usdc": D("15")}, "Rahmen"),
        ({"price_impact_pct": D("3")}, "Price Impact"),
    ]:
        gate = check_order(ctl, **{**base, **change})
        assert not gate.allowed and any(word in r for r in gate.reasons), (
            change,
            gate.reasons,
        )


def test_api_outage_blocks_before_the_meeting(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector()

    def down(currency):
        raise ConnectionError("down")

    conn.get_available_funds = down
    out = cycle(ctl, store, conn, monkeypatch)
    assert "BLOCKIERT" in out["result"] and conn.buys == []


def test_fees_are_part_of_the_realised_loss(tmp_path, monkeypatch):
    # The real 2026-11-13 round trip: bought for 10.9906, sold for 10.9673 net.
    assert realised_pnl(D("10.990601087466"), D("10.9672558970688")) == D(
        "-0.0233451903972"
    )
    ctl, store = armed(tmp_path)
    conn = FakeConnector()
    cycle(ctl, store, conn, monkeypatch)
    cost = D(read_positions(store)["BTC-USDC"]["cost_usdc"])
    conn.sell_proceeds = cost - D("0.03")
    out = close_position(
        "BTC-USDC", controller=ctl, connector=conn, store=store, reason="test"
    )
    assert D(out["realised_pnl_usdc"]) == D("-0.03")
    assert store.read_ledger().total_loss() == D("0.03")
    assert "BTC-USDC" not in read_positions(store)


def test_emergency_stop_blocks_exits_too_and_says_so(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector()
    cycle(ctl, store, conn, monkeypatch)
    ctl.trigger_emergency_stop("manuell")
    out = close_position(
        "BTC-USDC", controller=ctl, connector=conn, store=store, reason="stop"
    )
    assert conn.sells == [] and "Position bleibt offen" in out["result"]


# ---- readiness report ------------------------------------------------------


class _Auth:
    def __init__(self, path):
        self.users = {"admin": {"role": "admin", "hash": "ab", "salt": "cd"}}
        self.path = path

    def audit(self, event, **data):
        with self.path.open("a") as fh:
            fh.write(event + "\n")


def test_readiness_is_not_ready_without_a_connector(tmp_path):
    ctl = ModeController(NATE_CONFIRMED_LIMITS, store=SafetyStore(tmp_path))
    report = run_readiness_check(controller=ctl, market_updated_at=time.time())
    assert report["verdict"] == NOT_READY and report["total"] == 14
    assert "Coinbase-Verbindung" in report["failed"]
    assert report["live_autonomous_enabled"] is False


def test_readiness_passes_only_with_full_evidence_and_arms_nothing(tmp_path):
    ctl = ModeController(NATE_CONFIRMED_LIMITS, store=SafetyStore(tmp_path / "state"))
    conn = FakeConnector()
    conn.orders = {
        oid: {"status": "FILLED", "side": w["side"], "filled_size": w["filled_size"]}
        for oid, w in KNOWN_ORDERS.items()
    }
    audit = tmp_path / "audit.jsonl"
    kw = dict(
        controller=ctl,
        connector=conn,
        auth_store=_Auth(audit),
        audit_file=audit,
        market_updated_at=time.time(),
        expected_portfolio_id=PORTFOLIO,
        known_orders=KNOWN_ORDERS,
    )
    report = run_readiness_check(**kw)
    assert report["verdict"] == READY, report["failed"]
    assert not ctl.autonomous_armed and ctl.mode is TradingMode.PAPER  # arms nothing
    assert conn.buys == [] and conn.sells == []
    for change in (
        {"expected_portfolio_id": "anderes"},
        {"market_updated_at": time.time() - 600},
        {"controller": ModeController(NATE_CONFIRMED_LIMITS)},
    ):
        assert run_readiness_check(**{**kw, **change})["verdict"] == NOT_READY
    conn.permissions["can_transfer"] = True
    assert run_readiness_check(**kw)["verdict"] == NOT_READY
