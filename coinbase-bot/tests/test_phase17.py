"""Phase 17 — connector conformance with the Coinbase Advanced Trade OpenAPI
spec (advanced-trade-spec.yaml). The spec's field names are pinned here against
a fake SDK client, so a future SDK change that renames a field is caught. No
real order is sent; every client is a fake."""

import time
from decimal import Decimal as D

import pytest

import trading_team.live_pipeline as lp
from coinbase_connector.connector import CoinbaseLiveConnector, ConnectorError
from trading_team.collaboration import DebateRoom, Opinion
from trading_team.core import RiskManager
from trading_team.modes import AUTONOMOUS_ACTIVATION_PHRASE, ModeController, TradingMode
from trading_team.persistence import SafetyStore
from trading_team.risk_config import NATE_CONFIRMED_LIMITS, live_risk_config

PORTFOLIO = "pf-own"
OTHER = "pf-other"


class SpecClient:
    """Fake SDK client whose responses carry exactly the spec's fields."""

    def __init__(self, can_transfer=False, accounts=None):
        self._can_transfer = can_transfer
        self._accounts = (
            accounts
            if accounts is not None
            else [
                {
                    "currency": "USDC",
                    "retail_portfolio_id": PORTFOLIO,
                    "available_balance": {"value": "17.10", "currency": "USDC"},
                    "hold": {"value": "0", "currency": "USDC"},
                },
            ]
        )

    def get_api_key_permissions(self):  # GetApiKeyPermissionsResponse
        return {
            "can_view": True,
            "can_trade": True,
            "can_transfer": self._can_transfer,
            "portfolio_uuid": PORTFOLIO,
            "portfolio_type": "DEFAULT",
        }

    def get_accounts(self, **k):  # GetAccountsResponse
        return {"accounts": self._accounts, "has_next": False, "cursor": ""}

    def get_product(self, p, **k):
        return {"product_id": p, "status": "online"}

    def list_orders(self, **k):
        return {"orders": []}

    def get_transaction_summary(self, **k):  # GetTransactionSummaryResponse
        return {"fee_tier": {"taker_fee_rate": "0.001", "maker_fee_rate": "0.0009"}}


def conn(**k):
    return CoinbaseLiveConnector(client=SpecClient(**k), max_quote_per_order="17.10")


def test_permission_fields_match_spec_and_transfer_key_is_refused():
    c = conn()
    assert c.permissions["can_view"] and c.permissions["can_trade"]
    assert c.permissions["portfolio_uuid"] == PORTFOLIO
    with pytest.raises(ConnectorError):
        conn(can_transfer=True)


def test_available_funds_reads_spec_balance_shape():
    assert conn().get_available_funds("USDC") == D("17.10")


def test_isolation_proof_passes_for_own_portfolio_only():
    assert conn().assert_portfolio_isolation()["portfolio_uuid"] == PORTFOLIO


def test_isolation_detects_foreign_portfolio_account():
    foreign = [
        {
            "currency": "USDC",
            "retail_portfolio_id": OTHER,
            "available_balance": {"value": "500", "currency": "USDC"},
            "hold": {"value": "0", "currency": "USDC"},
        }
    ]
    c = conn(accounts=foreign)
    with pytest.raises(ConnectorError):
        c.assert_portfolio_isolation()
    assert c.get_available_funds("USDC") == D("0")  # foreign funds never spendable
    assert c.verify_access(expected_portfolio_id=PORTFOLIO)["ok"] is False


def test_preview_metrics_reads_spec_fields_and_never_guesses():
    m = CoinbaseLiveConnector.preview_metrics(
        {
            "order_total": "11.00",
            "commission_total": "0.011",
            "slippage": "0.3",
            "best_bid": "68000",
            "best_ask": "68010",
            "preview_id": "pv-1",
        }
    )
    assert m["slippage_pct"] == D("0.3") and m["commission_total"] == D("0.011")
    assert m["best_ask"] == D("68010") and m["preview_id"] == "pv-1"
    empty = CoinbaseLiveConnector.preview_metrics({})
    assert empty["slippage_pct"] is None and empty["commission_total"] is None


def test_error_detail_extracts_spec_error_shape():
    class ApiError(Exception):
        pass

    exc = ApiError("boom")
    exc.response = {"error": "INVALID_ARGUMENT", "code": 3, "message": "bad size"}
    d = CoinbaseLiveConnector.error_detail(exc)
    assert (d["error"], d["code"], d["message"]) == ("INVALID_ARGUMENT", 3, "bad size")
    assert CoinbaseLiveConnector.error_detail(ValueError("x"))["type"] == "ValueError"


def test_verify_access_includes_isolation_proof_and_fees():
    report = conn().verify_access(expected_portfolio_id=PORTFOLIO)
    assert report["ok"] and report["checks"]["portfolio_isolated"]
    assert report["checks"]["isolation_proof"]["portfolio_uuid"] == PORTFOLIO
    assert report["checks"]["fees"]["taker_fee_rate"] == "0.001"
    assert report["checks"]["cannot_transfer"]


class PreviewConn:
    permissions = {
        "can_view": True,
        "can_trade": True,
        "can_transfer": False,
        "portfolio_uuid": PORTFOLIO,
    }

    def __init__(self, preview):
        self.preview, self.buys = preview, []

    def get_available_funds(self, c):
        return D("17.10")

    def get_open_orders(self):
        return []

    def get_market_price(self, p):
        return {"bid": D("100"), "ask": D("130")}  # crude approx: ~13 %

    def preview_buy_order(self, p, q):
        return dict(self.preview)

    def preview_metrics(self, preview):
        return CoinbaseLiveConnector.preview_metrics(preview)

    def execute_real_buy(self, p, q, cid, conf):
        self.buys.append(q)
        self._o = {
            "order_id": "o1",
            "status": "FILLED",
            "side": "BUY",
            "filled_size": "0.0001",
            "total_value_after_fees": q,
            "total_fees": "0.01",
            "client_order_id": cid,
        }
        return {"order_id": "o1"}

    def get_real_order_status(self, oid):
        return self._o


def _cycle(tmp_path, monkeypatch, connector):
    store = SafetyStore(tmp_path)
    ctl = ModeController(NATE_CONFIRMED_LIMITS, store=store)
    ctl.arm_autonomous(AUTONOMOUS_ACTIVATION_PHRASE, True, armed_by="pytest")
    ctl.set_mode(TradingMode.LIVE_AUTONOMOUS)
    real = lp.hold_meeting

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

    monkeypatch.setattr(lp, "hold_meeting", patched)
    closes = [D(str(100 + i * 0.5)) for i in range(60)]
    return lp.run_cycle(
        "BTC-USDC",
        closes,
        controller=ctl,
        risk=RiskManager(live_risk_config()),
        connector=connector,
        store=store,
        market_updated_at=time.time(),
        fee_rate=D("0.001"),
        min_order_usdc=D("1"),
    )


def test_run_cycle_prefers_preview_native_slippage(tmp_path, monkeypatch):
    c = PreviewConn({"slippage": "0.2", "commission_total": "0.01"})
    out = _cycle(tmp_path, monkeypatch, c)
    assert out["steps"]["preview"]["slippage_source"] == "preview"
    assert out["steps"]["preview"]["slippage_pct"] == "0.2"
    assert out["sent"] is True and len(c.buys) == 1


def test_run_cycle_blocks_when_preview_slippage_exceeds_limit(tmp_path, monkeypatch):
    c = PreviewConn({"slippage": "3.5", "commission_total": "0.01"})
    out = _cycle(tmp_path, monkeypatch, c)
    assert out["sent"] is False and c.buys == [] and "Slippage" in out["result"]


def test_run_cycle_falls_back_to_quote_when_preview_lacks_slippage(
    tmp_path, monkeypatch
):
    c = PreviewConn({"commission_total": "0.01"})  # no slippage field
    out = _cycle(tmp_path, monkeypatch, c)
    assert out["steps"]["preview"]["slippage_source"] == "quote"
    assert out["sent"] is False and c.buys == []  # crude 13 % > 2 % limit


# ---- 6/7 order lookup scoped to own portfolio + fill reconciliation --------

class OrdersClient(SpecClient):
    def __init__(self, fills, order):
        super().__init__()
        self.calls, self._fills, self._order = [], fills, order

    def list_orders(self, **k):
        self.calls.append(("list_orders", k))
        page = k.get("cursor")
        if page is None:
            return {"orders": [{"client_order_id": "a"}], "has_next": True, "cursor": "p2"}
        return {"orders": [{"client_order_id": "hg-x", "order_id": "o9"}], "has_next": False}

    def get_fills(self, **k):
        self.calls.append(("get_fills", k))
        return {"fills": self._fills, "cursor": ""}

    def get_order(self, order_id):
        return {"order": self._order}


# The real BUY of 2026-11-13: one fill, 0.00016017 BTC, fee 0.010979621466.
REAL_ORDER = {"order_id": "66b81bf7", "status": "FILLED", "filled_size": "0.00016017",
              "total_fees": "0.010979621466"}
REAL_FILLS = [{"size": "0.00016017", "commission": "0.010979621466", "price": "68549.8"}]


def test_order_queries_are_scoped_to_own_portfolio_and_paginate():
    client = OrdersClient(REAL_FILLS, REAL_ORDER)
    c = CoinbaseLiveConnector(client=client, max_quote_per_order="17.10")
    assert c.find_order_by_client_id("hg-x")["order_id"] == "o9"     # found on page 2
    c.get_open_orders()
    c.get_real_fills("66b81bf7")
    for name, kwargs in client.calls:
        assert kwargs.get("retail_portfolio_id") == PORTFOLIO, name


def test_fill_reconciliation_matches_real_order():
    c = CoinbaseLiveConnector(client=OrdersClient(REAL_FILLS, REAL_ORDER),
                              max_quote_per_order="17.10")
    r = c.reconcile_fills("66b81bf7")
    assert r["match"] and r["fills"] == 1


def test_fill_reconciliation_flags_mismatch():
    partial = [{"size": "0.00010000", "commission": "0.0068"}]
    c = CoinbaseLiveConnector(client=OrdersClient(partial, REAL_ORDER),
                              max_quote_per_order="17.10")
    assert c.reconcile_fills("66b81bf7")["match"] is False


# Real fills of 2026-11-13, read from Coinbase. The BUY was quote-sized, so its
# single fill reports size in USDC (size_in_quote=true); the SELL had three
# base-sized fills.
REAL_BUY_FILLS = [{"size": "10.979621466", "size_in_quote": True, "price": "68549.8",
                   "commission": "0.010979621466"}]
REAL_SELL_ORDER = {"order_id": "fcda9f60", "status": "FILLED",
                   "filled_size": "0.00016017", "total_fees": "0.0109782341312"}
REAL_SELL_FILLS = [
    {"size": "0.00014042", "size_in_quote": False, "price": "68541.11",
     "commission": "0.0096245426662"},
    {"size": "0.0000191", "size_in_quote": False, "price": "68541.34",
     "commission": "0.001309139594"},
    {"size": "0.00000065", "size_in_quote": False, "price": "68541.34",
     "commission": "0.000044551871"},
]


def test_reconcile_real_quote_sized_buy():
    c = CoinbaseLiveConnector(client=OrdersClient(REAL_BUY_FILLS, REAL_ORDER),
                              max_quote_per_order="17.10")
    r = c.reconcile_fills("66b81bf7")
    assert r["match"], r
    assert D(r["fill_size"]) == D("0.00016017")


def test_reconcile_real_three_fill_sell():
    c = CoinbaseLiveConnector(client=OrdersClient(REAL_SELL_FILLS, REAL_SELL_ORDER),
                              max_quote_per_order="17.10")
    r = c.reconcile_fills("fcda9f60")
    assert r["match"] and r["fills"] == 3, r
