"""Tests for the connector's safety guards.

The fakes only stand in for the network in tests. The connector itself has no
simulated mode.
"""

import os

import pytest
from eth_account import Account

from hl_connector import (
    ConnectorError,
    HyperliquidSpotConnector,
    LiveTradingBlocked,
    load_env_file,
)

MAIN = "0x00000000000000000000000000000000000000AA"


class FakeInfo:
    def __init__(self, usdc="100", ubtc="0.001", agent_of=MAIN):
        self.usdc, self.ubtc, self.agent_of = usdc, ubtc, agent_of

    def post(self, path, body):
        if body["user"] == MAIN:
            return {"role": "user"}
        if self.agent_of:
            return {"role": "agent", "data": {"user": self.agent_of}}
        return {"role": "missing"}

    def spot_meta(self):
        return {
            "tokens": [
                {"index": 0, "name": "USDC", "szDecimals": 8},
                {"index": 1, "name": "UBTC", "szDecimals": 5},
            ],
            "universe": [{"name": "@142", "index": 142, "tokens": [1, 0]}],
        }

    def spot_user_state(self, address):
        return {
            "balances": [
                {"coin": "USDC", "total": self.usdc, "hold": "0"},
                {"coin": "UBTC", "total": self.ubtc, "hold": "0"},
            ]
        }

    def l2_snapshot(self, name):
        return {"levels": [[{"px": "70000", "sz": "1"}], [{"px": "70010", "sz": "1"}]]}

    def user_fees(self, address):
        return {"userSpotCrossRate": "0.0007"}

    def user_fills(self, address):
        return [{"oid": 7, "sz": "0.00017"}, {"oid": 8, "sz": "1"}]


class FakeExchange:
    def __init__(self, status=None):
        self.status = status or {
            "filled": {"totalSz": "0.00017", "avgPx": "70010", "oid": 7}
        }
        self.sent = []

    def order(self, name, is_buy, sz, limit_px, order_type, cloid=None):
        self.sent.append((name, is_buy, sz, limit_px))
        return {"status": "ok", "response": {"data": {"statuses": [self.status]}}}


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv("HL_LIVE_TRADING_ENABLED", "1")


def make(tmp_path, info=None, exchange=None, **kwargs):
    exchange = exchange or FakeExchange()
    connector = HyperliquidSpotConnector(
        MAIN,
        info=info or FakeInfo(),
        exchange=exchange,
        wallet=Account.create(),
        state_dir=tmp_path,
        **kwargs
    )
    return connector, exchange


def test_perpetual_or_unknown_pair_is_refused(tmp_path):
    connector, _ = make(tmp_path)
    with pytest.raises(ConnectorError, match="Spot only"):
        connector.prepare_buy_order("BTC", "12")


def test_prepare_rounds_size_down_and_estimates_fee(tmp_path):
    connector, _ = make(tmp_path)
    order = connector.prepare_buy_order("UBTC/USDC", "12")
    assert order["size"] == "0.00017"
    assert order["asset"] == 10142
    assert order["limit_px"] == "70710.0"
    assert order["confirmation"] == "EXECUTE BUY UBTC/USDC 0.00017 LIMIT 70710.0"
    assert float(order["est_fee"]) == pytest.approx(0.00017 * 70010 * 0.0007)


def test_order_below_minimum_value_is_refused(tmp_path):
    connector, _ = make(tmp_path)
    with pytest.raises(ConnectorError, match="minimum"):
        connector.prepare_buy_order("UBTC/USDC", "5")


def test_prepare_fails_without_funds(tmp_path):
    connector, _ = make(tmp_path, info=FakeInfo(usdc="0"))
    with pytest.raises(ConnectorError, match="Insufficient USDC"):
        connector.prepare_buy_order("UBTC/USDC", "12")
    with pytest.raises(ConnectorError, match="Insufficient UBTC"):
        connector.prepare_sell_order("UBTC/USDC", "0.01")


def test_sign_order_is_local_and_sends_nothing(tmp_path):
    connector, exchange = make(tmp_path)
    signed = connector.sign_order(connector.prepare_buy_order("UBTC/USDC", "12"))
    assert signed["signer"] == connector.api_wallet_address()
    assert set(signed["signature"]) == {"r", "s", "v"}
    assert exchange.sent == []


def test_buy_blocked_without_live_flag(tmp_path, monkeypatch):
    monkeypatch.delenv("HL_LIVE_TRADING_ENABLED", raising=False)
    connector, exchange = make(tmp_path)
    order = connector.prepare_buy_order("UBTC/USDC", "12")
    with pytest.raises(LiveTradingBlocked):
        connector.execute_real_buy(order, order["confirmation"])
    assert exchange.sent == []


def test_blocked_when_confirmation_or_side_differs(tmp_path, live):
    connector, exchange = make(tmp_path)
    order = connector.prepare_buy_order("UBTC/USDC", "12")
    with pytest.raises(LiveTradingBlocked):
        connector.execute_real_buy(order, "EXECUTE BUY UBTC/USDC 1 LIMIT 70710.0")
    with pytest.raises(LiveTradingBlocked):
        connector.execute_real_sell(order, order["confirmation"])
    assert exchange.sent == []


def test_blocked_above_capital_limit(tmp_path, live):
    connector, exchange = make(tmp_path)
    order = connector.prepare_buy_order("UBTC/USDC", "50")
    with pytest.raises(LiveTradingBlocked, match="limit"):
        connector.execute_real_buy(order, order["confirmation"])
    assert exchange.sent == []


def test_tampered_order_pointing_at_a_perp_asset_is_blocked(tmp_path, live):
    connector, exchange = make(tmp_path)
    order = connector.prepare_buy_order("UBTC/USDC", "12")
    order["asset"], order["name"] = 0, "BTC"
    with pytest.raises(LiveTradingBlocked, match="spot"):
        connector.execute_real_buy(order, order["confirmation"])
    assert exchange.sent == []


def test_approved_order_is_sent_once_and_never_twice(tmp_path, live):
    connector, exchange = make(tmp_path)
    order = connector.prepare_buy_order("UBTC/USDC", "12")
    status = connector.execute_real_buy(order, order["confirmation"])
    assert status["filled"]["oid"] == 7
    assert exchange.sent == [("@142", True, 0.00017, 70710.0)]
    with pytest.raises(LiveTradingBlocked, match="already submitted"):
        connector.execute_real_buy(order, order["confirmation"])
    assert len(exchange.sent) == 1


def test_kill_switch_blocks_everything(tmp_path, live):
    connector, exchange = make(tmp_path)
    order = connector.prepare_buy_order("UBTC/USDC", "12")
    connector.emergency_stop("test")
    with pytest.raises(LiveTradingBlocked, match="Kill switch"):
        connector.execute_real_buy(order, order["confirmation"])
    assert exchange.sent == []


def test_exchange_error_raises(tmp_path, live):
    connector, _ = make(
        tmp_path, exchange=FakeExchange(status={"error": "Insufficient balance"})
    )
    order = connector.prepare_buy_order("UBTC/USDC", "12")
    with pytest.raises(ConnectorError, match="Insufficient balance"):
        connector.execute_real_buy(order, order["confirmation"])


def test_api_wallet_authorization_requires_matching_owner(tmp_path):
    assert make(tmp_path)[0].api_wallet_authorized() is True
    assert (
        make(tmp_path, info=FakeInfo(agent_of=None))[0].api_wallet_authorized() is False
    )
    other = "0x00000000000000000000000000000000000000BB"
    assert (
        make(tmp_path, info=FakeInfo(agent_of=other))[0].api_wallet_authorized()
        is False
    )


def test_fills_are_filtered_by_order(tmp_path):
    assert make(tmp_path)[0].get_order_fills(7) == [{"oid": 7, "sz": "0.00017"}]


def test_invalid_key_error_does_not_leak_the_value(tmp_path, monkeypatch):
    monkeypatch.setenv("HL_API_WALLET_KEY", "not-a-key-value")
    with pytest.raises(ConnectorError) as error:
        HyperliquidSpotConnector(MAIN, info=FakeInfo(), state_dir=tmp_path)
    assert "not-a-key-value" not in str(error.value)


def test_env_file_fills_missing_values_only(tmp_path, monkeypatch):
    monkeypatch.setenv("HL_MAIN_WALLET_ADDRESS", "from-env")
    monkeypatch.delenv("HL_TEST_OTHER", raising=False)
    file = tmp_path / ".env.local"
    file.write_text(
        "# comment\nHL_MAIN_WALLET_ADDRESS=from-file\nHL_TEST_OTHER=x\nEMPTY=\n"
    )
    load_env_file(file)
    assert os.environ["HL_MAIN_WALLET_ADDRESS"] == "from-env"
    assert os.environ["HL_TEST_OTHER"] == "x"
    assert "EMPTY" not in os.environ
