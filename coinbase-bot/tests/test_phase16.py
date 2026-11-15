"""Phase 15/16: championship, runner (paper + live), position monitor,
stop-loss / take-profit / time exits, and the read-only connector verification.
No test sends a real order; every connector here is a fake that records calls."""

import time
from decimal import Decimal as D

import pytest

from coinbase_connector.connector import CoinbaseLiveConnector
from trading_team import engine
from trading_team.core import RiskManager
from trading_team.engine import (
    ExitRule,
    monitor_positions,
    paper_buy,
    read_paper_ledger,
    read_paper_positions,
    run_championship,
    run_once,
)
from trading_team.live_pipeline import read_positions
from trading_team.modes import AUTONOMOUS_ACTIVATION_PHRASE, ModeController, TradingMode
from trading_team.persistence import SafetyStore
from trading_team.risk_config import NATE_CONFIRMED_LIMITS, live_risk_config

PORTFOLIO = "pf-test"


def ohlcv(n=60, start=100.0, step=0.0, vol=1000.0, last_jump=0.0):
    """Synthetic completed bars. step>0 trends up; last_jump spikes the final close."""
    bars = []
    for i in range(n):
        c = start + i * step
        if i == n - 1:
            c += last_jump
        bars.append(
            {
                "o": c - step / 2 if step else c,
                "h": c + 1,
                "l": c - 1,
                "c": c,
                "v": vol * (3 if i == n - 1 and last_jump else 1),
            }
        )
    return bars


class FakeConnector:
    sell_proceeds = D("0")

    def __init__(self, usdc="17.10"):
        self.usdc = D(usdc)
        self.buys, self.sells, self.orders = [], [], {}
        self.permissions = {
            "can_view": True,
            "can_trade": True,
            "can_transfer": False,
            "portfolio_uuid": PORTFOLIO,
        }
        self.bid, self.ask = D("129.45"), D("129.55")

    def get_available_funds(self, c):
        return self.usdc

    def get_open_orders(self):
        return []

    def get_market_price(self, p):
        return {"bid": self.bid, "ask": self.ask}

    def preview_buy_order(self, p, quote_size):
        return {"quote_size": quote_size}

    def execute_real_buy(self, p, quote_size, cid, confirmation):
        self.buys.append((p, quote_size, cid))
        oid = f"o-{len(self.buys)}"
        self.orders[oid] = {
            "order_id": oid,
            "client_order_id": cid,
            "side": "BUY",
            "status": "FILLED",
            "filled_size": str((D(quote_size) / self.ask).quantize(D("0.00000001"))),
            "total_value_after_fees": quote_size,
            "total_fees": str(D(quote_size) * D("0.001")),
        }
        return {"order_id": oid}

    def execute_real_sell(self, p, base_size, cid, confirmation):
        self.sells.append((p, base_size, cid))
        oid = f"s-{len(self.sells)}"
        self.orders[oid] = {
            "order_id": oid,
            "client_order_id": cid,
            "side": "SELL",
            "status": "FILLED",
            "filled_size": base_size,
            "total_value_after_fees": str(self.sell_proceeds),
            "total_fees": "0.01",
        }
        return {"order_id": oid}

    def get_real_order_status(self, oid):
        return self.orders[oid]

    def find_order_by_client_id(self, cid):
        return next(
            (o for o in self.orders.values() if o["client_order_id"] == cid), None
        )


def paper_ctl(tmp_path):
    store = SafetyStore(tmp_path)
    return ModeController(NATE_CONFIRMED_LIMITS, store=store), store


def armed(tmp_path):
    store = SafetyStore(tmp_path)
    ctl = ModeController(NATE_CONFIRMED_LIMITS, store=store)
    ctl.arm_autonomous(AUTONOMOUS_ACTIVATION_PHRASE, True, armed_by="pytest")
    ctl.set_mode(TradingMode.LIVE_AUTONOMOUS)
    return ctl, store


def force_buy_champ(monkeypatch):
    monkeypatch.setattr(
        engine,
        "run_championship",
        lambda bars, **k: {
            "winner_side": "BUY",
            "buy_votes": 5,
            "sell_votes": 0,
            "quorum": 3,
            "ranked": [],
            "note": "forced BUY",
        },
    )


def force_buy_meeting(monkeypatch):
    # The PAPER path calls engine.hold_meeting; the LIVE path calls
    # live_pipeline.hold_meeting inside run_cycle. Patch both namespaces.
    from trading_team import engine as eng
    from trading_team import live_pipeline as lp
    from trading_team.collaboration import DebateRoom, Opinion

    real = eng.hold_meeting

    def patched(*a, **k):
        k.setdefault(
            "room",
            DebateRoom(
                voices=[
                    (lambda r, c, nm=nm: Opinion(nm, "BUY", D("0.9"), "t"))
                    for nm in ("A", "B", "C")
                ]
            ),
        )
        return real(*a, **k)

    monkeypatch.setattr(eng, "hold_meeting", patched)
    monkeypatch.setattr(lp, "hold_meeting", patched)


def runner_kwargs(ctl, store, conn, mode):
    return dict(
        controller=ctl,
        risk=RiskManager(live_risk_config()),
        connector=conn,
        store=store,
        market_updated_at=time.time(),
        fee_rate=D("0.001"),
        min_order_usdc=D("1"),
        mode=mode,
    )


# ---- championship ----------------------------------------------------------


def test_championship_ranks_all_seven_and_is_long_only_for_entries():
    champ = run_championship(ohlcv(60, step=0.0))  # flat / no uptrend
    # The runner only enters on a BUY winner; a flat/weak tape must NOT be BUY.
    assert champ["winner_side"] != "BUY" and len(champ["ranked"]) == 7
    assert {v["name"] for v in champ["ranked"]} >= {"macd_trend", "mean_reversion"}


def test_championship_is_honest_about_votes():
    champ = run_championship(ohlcv(80, start=100, step=1.5, last_jump=8))
    assert champ["winner_side"] in ("BUY", "HOLD")  # real strategies, honest outcome
    assert champ["buy_votes"] + champ["sell_votes"] <= 7


# ---- runner: one shared execution, no double spend -------------------------


def test_paper_runner_simulates_a_fill_with_real_fee_and_no_real_order(
    tmp_path, monkeypatch
):
    ctl, store = paper_ctl(tmp_path)
    conn = FakeConnector()
    force_buy_champ(monkeypatch)
    force_buy_meeting(monkeypatch)
    out = run_once(
        "BTC-USDC",
        ohlcv(60, step=0.5),
        **runner_kwargs(ctl, store, conn, TradingMode.PAPER),
    )
    assert out["sent"] and conn.buys == [] and conn.sells == []
    pos = read_paper_positions(store)["BTC-USDC"]
    assert D(pos["fees_usdc"]) > 0 and read_positions(store) == {}
    again = run_once(
        "BTC-USDC",
        ohlcv(60, step=0.5),
        **runner_kwargs(ctl, store, conn, TradingMode.PAPER),
    )
    assert again["sent"] is False and "besteht bereits" in again["result"]


def test_paper_runner_blocks_entries_under_emergency_stop(tmp_path, monkeypatch):
    ctl, store = paper_ctl(tmp_path)
    ctl.trigger_emergency_stop("test")
    force_buy_champ(monkeypatch)
    out = run_once(
        "BTC-USDC",
        ohlcv(60, step=0.5),
        **runner_kwargs(ctl, store, FakeConnector(), TradingMode.PAPER),
    )
    assert out["sent"] is False and "Not-Aus" in out["result"]


def test_hold_championship_means_no_meeting_and_no_order(tmp_path):
    ctl, store = paper_ctl(tmp_path)
    out = run_once(
        "BTC-USDC",
        ohlcv(60, step=0.0),
        **runner_kwargs(ctl, store, FakeConnector(), TradingMode.PAPER),
    )
    assert out["sent"] is False and "Championship" in out["result"]


def test_live_runner_routes_through_real_cycle(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector()
    force_buy_champ(monkeypatch)
    force_buy_meeting(monkeypatch)
    out = run_once(
        "BTC-USDC",
        ohlcv(60, step=0.5),
        **runner_kwargs(ctl, store, conn, TradingMode.LIVE_AUTONOMOUS),
    )
    assert out["sent"] and len(conn.buys) == 1 and read_paper_positions(store) == {}


# ---- monitor: stop-loss, take-profit, time, stale --------------------------


def test_paper_stop_loss_then_ledger_booked(tmp_path):
    ctl, store = paper_ctl(tmp_path)
    paper_buy(
        "BTC-USDC",
        D("10"),
        D("100"),
        store=store,
        fee_rate=D("0.001"),
        stop_loss="90",
        take_profit="120",
        now=1000.0,
    )
    r = monitor_positions(
        {"BTC-USDC": {"price": 100.0}},
        controller=ctl,
        connector=None,
        store=store,
        paper=True,
        now=1001.0,
    )
    assert r["actions"] == [] and r["watch_blocked"] == []
    r = monitor_positions(
        {"BTC-USDC": {"price": 89.0}},
        controller=ctl,
        connector=None,
        store=store,
        paper=True,
        now=1002.0,
    )
    assert len(r["actions"]) == 1 and "Stop-Loss" in r["actions"][0]["reason"]
    assert read_paper_positions(store) == {}
    assert read_paper_ledger(store)["total_realised"] < 0


def test_paper_take_profit_fires(tmp_path):
    ctl, store = paper_ctl(tmp_path)
    paper_buy(
        "ETH-USDC",
        D("10"),
        D("100"),
        store=store,
        fee_rate=D("0.001"),
        stop_loss="90",
        take_profit="120",
        now=1000.0,
    )
    r = monitor_positions(
        {"ETH-USDC": {"price": 125.0}},
        controller=ctl,
        connector=None,
        store=store,
        paper=True,
        now=1001.0,
    )
    assert "Take-Profit" in r["actions"][0]["reason"]


def test_paper_time_exit(tmp_path):
    ctl, store = paper_ctl(tmp_path)
    paper_buy(
        "SOL-USDC",
        D("10"),
        D("100"),
        store=store,
        fee_rate=D("0.001"),
        stop_loss="1",
        take_profit="9999",
        now=1000.0,
    )
    r = monitor_positions(
        {"SOL-USDC": {"price": 100.0}},
        controller=ctl,
        connector=None,
        store=store,
        paper=True,
        rule=ExitRule(max_hold_seconds=60),
        now=1000.0 + 120,
    )
    assert "Zeit-Exit" in r["actions"][0]["reason"]


def test_monitor_never_acts_on_stale_or_missing_price(tmp_path):
    ctl, store = paper_ctl(tmp_path)
    paper_buy(
        "BTC-USDC",
        D("10"),
        D("100"),
        store=store,
        fee_rate=D("0.001"),
        stop_loss="99999",
        take_profit="120",
        now=1000.0,
    )
    stale = monitor_positions(
        {"BTC-USDC": {"price": 50.0}},
        controller=ctl,
        connector=None,
        store=store,
        paper=True,
        market_stale=True,
        now=1001.0,
    )
    missing = monitor_positions(
        {}, controller=ctl, connector=None, store=store, paper=True, now=1001.0
    )
    for r in (stale, missing):
        assert r["actions"] == [] and len(r["watch_blocked"]) == 1
    assert "BTC-USDC" in read_paper_positions(
        store
    )  # position stays, keeps being watched


def test_live_monitor_stop_loss_fires_even_under_emergency_stop(tmp_path, monkeypatch):
    ctl, store = armed(tmp_path)
    conn = FakeConnector()
    force_buy_champ(monkeypatch)
    force_buy_meeting(monkeypatch)
    run_once(
        "BTC-USDC",
        ohlcv(60, step=0.5),
        **runner_kwargs(ctl, store, conn, TradingMode.LIVE_AUTONOMOUS),
    )
    pos = read_positions(store)["BTC-USDC"]
    stop = D(pos["stop_loss"])
    ctl.trigger_emergency_stop("Crash")
    conn.sell_proceeds = D(pos["cost_usdc"]) - D("1")
    r = monitor_positions(
        {"BTC-USDC": {"price": float(stop) - 1}},
        controller=ctl,
        connector=conn,
        store=store,
        paper=False,
        now=time.time(),
    )
    assert len(conn.sells) == 1 and "Stop-Loss" in r["actions"][0]["reason"]
    assert read_positions(store) == {}  # flattened despite the stop


# ---- connector read-only verification + order types ------------------------


def test_supported_order_types_is_honest_about_no_guarantee():
    types = CoinbaseLiveConnector.supported_order_types()
    assert "market" in types and "stop_limit" in types and "trigger_bracket" in types
    assert "NO order type guarantees" in types["guarantee"]


def test_verify_access_read_only_passes_and_sends_nothing():
    class ReadOnlyClient:
        def get_api_key_permissions(self):
            return {
                "can_view": True,
                "can_trade": True,
                "can_transfer": False,
                "portfolio_uuid": PORTFOLIO,
            }

        def get_accounts(self, **k):
            return {
                "accounts": [
                    {
                        "currency": "USDC",
                        "available_balance": {"value": "17.10", "currency": "USDC"},
                    }
                ],
                "has_next": False,
            }

        def get_product(self, p, **k):
            return {"product_id": p, "status": "online"}

        def list_orders(self, **k):
            return {"orders": []}

        def get_transaction_summary(self, **k):
            return {"fee_tier": {"taker_fee_rate": "0.001"}}

    conn = CoinbaseLiveConnector(client=ReadOnlyClient(), max_quote_per_order="17.10")
    report = conn.verify_access(expected_portfolio_id=PORTFOLIO)
    assert report["ok"] and report["checks"]["portfolio_isolated"]
    assert report["checks"]["cannot_transfer"]
    assert conn.verify_access(expected_portfolio_id="anderes")["ok"] is False


def test_verify_access_rejects_transfer_permission():
    class TransferClient:
        def get_api_key_permissions(self):
            return {"can_view": True, "can_trade": True, "can_transfer": True}

    with pytest.raises(Exception):
        CoinbaseLiveConnector(client=TransferClient(), max_quote_per_order="17.10")
