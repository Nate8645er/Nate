"""Tests for the connector's safety guards.

The fake client only stands in for the network in tests. The connector itself
has no simulated mode.
"""

import pytest

from coinbase_connector import (
    CoinbaseLiveConnector,
    ConnectorError,
    LiveTradingBlocked,
    confirmation_phrase,
)


class FakeClient:
    def __init__(self, can_trade=True, can_transfer=False, order_success=True):
        self.perms = {
            "can_view": True,
            "can_trade": can_trade,
            "can_transfer": can_transfer,
        }
        self.order_success = order_success
        self.sent = []

    def get_api_key_permissions(self):
        return self.perms

    def get_accounts(self, limit=None, cursor=None):
        if cursor is None:
            return {
                "accounts": [
                    {"currency": "EUR", "available_balance": {"value": "5.50"}}
                ],
                "has_next": True,
                "cursor": "next",
            }
        return {
            "accounts": [{"currency": "BTC", "available_balance": {"value": "0.0001"}}],
            "has_next": False,
        }

    def get_best_bid_ask(self, product_ids=None):
        return {
            "pricebooks": [{"bids": [{"price": "60000"}], "asks": [{"price": "60010"}]}]
        }

    def preview_market_order_buy(self, product_id, quote_size=None):
        return {"errs": ["PREVIEW_INSUFFICIENT_FUND"]}

    def _order(self, side, client_order_id, product_id):
        self.sent.append((side, client_order_id, product_id))
        if self.order_success:
            return {"success": True, "success_response": {"order_id": "abc"}}
        return {"success": False, "error_response": {"error": "INSUFFICIENT_FUND"}}

    def market_order_buy(self, client_order_id, product_id, quote_size=None):
        return self._order("BUY", client_order_id, product_id)

    def market_order_sell(self, client_order_id, product_id, base_size=None):
        return self._order("SELL", client_order_id, product_id)

    def cancel_orders(self, order_ids):
        return {
            "results": [{"success": False, "failure_reason": "UNKNOWN_CANCEL_ORDER"}]
        }


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "1")


def test_refuses_key_with_transfer_permission():
    with pytest.raises(ConnectorError, match="transfer"):
        CoinbaseLiveConnector(FakeClient(can_transfer=True))


def test_balance_follows_pagination():
    connector = CoinbaseLiveConnector(FakeClient())
    assert len(connector.get_real_balance()) == 2
    assert str(connector.get_available_funds("btc")) == "0.0001"
    assert str(connector.get_available_funds("USDC")) == "0"


def test_preview_error_is_raised_not_hidden():
    with pytest.raises(ConnectorError, match="PREVIEW_INSUFFICIENT_FUND"):
        CoinbaseLiveConnector(FakeClient()).preview_buy_order("BTC-EUR", "2.00")


def test_buy_blocked_without_live_flag(monkeypatch):
    monkeypatch.delenv("LIVE_TRADING_ENABLED", raising=False)
    client = FakeClient()
    with pytest.raises(LiveTradingBlocked):
        CoinbaseLiveConnector(client).execute_real_buy(
            "BTC-EUR", "2.00", "id-1", confirmation_phrase("BUY", "BTC-EUR", "2.00")
        )
    assert client.sent == []


def test_buy_blocked_when_confirmation_differs(live):
    client = FakeClient()
    with pytest.raises(LiveTradingBlocked):
        CoinbaseLiveConnector(client).execute_real_buy(
            "BTC-EUR", "5.00", "id-1", confirmation_phrase("BUY", "BTC-EUR", "2.00")
        )
    assert client.sent == []


def test_buy_blocked_above_order_limit(live):
    client = FakeClient()
    with pytest.raises(LiveTradingBlocked, match="limit"):
        CoinbaseLiveConnector(client).execute_real_buy(
            "BTC-EUR", "50.00", "id-1", confirmation_phrase("BUY", "BTC-EUR", "50.00")
        )
    assert client.sent == []


def test_sell_blocked_above_order_limit(live):
    client = FakeClient()
    with pytest.raises(LiveTradingBlocked, match="limit"):
        CoinbaseLiveConnector(client).execute_real_sell(
            "BTC-EUR", "1", "id-1", confirmation_phrase("SELL", "BTC-EUR", "1")
        )
    assert client.sent == []


def test_approved_buy_and_sell_are_sent_once_with_client_order_id(live):
    client = FakeClient()
    connector = CoinbaseLiveConnector(client)
    buy = connector.execute_real_buy(
        "BTC-EUR", "2.00", "id-1", confirmation_phrase("BUY", "BTC-EUR", "2.00")
    )
    connector.execute_real_sell(
        "BTC-EUR", "0.00003", "id-2", confirmation_phrase("SELL", "BTC-EUR", "0.00003")
    )
    assert buy == {"order_id": "abc"}
    assert client.sent == [("BUY", "id-1", "BTC-EUR"), ("SELL", "id-2", "BTC-EUR")]


def test_rejected_order_raises(live):
    with pytest.raises(ConnectorError, match="INSUFFICIENT_FUND"):
        CoinbaseLiveConnector(FakeClient(order_success=False)).execute_real_buy(
            "BTC-EUR", "2.00", "id-1", confirmation_phrase("BUY", "BTC-EUR", "2.00")
        )


def test_key_without_trade_permission_cannot_order(live):
    client = FakeClient(can_trade=False)
    with pytest.raises(ConnectorError, match="trade permission"):
        CoinbaseLiveConnector(client).execute_real_buy(
            "BTC-EUR", "2.00", "id-1", confirmation_phrase("BUY", "BTC-EUR", "2.00")
        )
    assert client.sent == []


def test_failed_cancel_raises():
    with pytest.raises(ConnectorError, match="Cancel failed"):
        CoinbaseLiveConnector(FakeClient()).cancel_open_order("abc")
