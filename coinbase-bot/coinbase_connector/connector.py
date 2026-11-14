"""Minimal Coinbase live execution connector (Advanced Trade API, official SDK).

Every method talks to the real Coinbase API. There is no paper mode, no
simulated balance and no fallback: if a call fails, it raises.

Safety rules enforced here:
  * The connector refuses to start with an API key that can transfer funds.
  * execute_real_buy / execute_real_sell need LIVE_TRADING_ENABLED=1 and a
    confirmation string that repeats the exact order, so an order can never be
    sent by accident or with different parameters than the ones approved.
  * Each order carries a caller-supplied client_order_id. Coinbase rejects a
    second order with the same id, which makes retries idempotent.
  * A created order is NOT a filled order. Callers must read the result back
    with get_real_order_status() and get_real_fills().
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

LIVE_FLAG = "LIVE_TRADING_ENABLED"


class ConnectorError(RuntimeError):
    """Coinbase rejected a request or returned something unusable."""


class LiveTradingBlocked(ConnectorError):
    """A real order was requested without the required approval."""


def _as_dict(response: Any) -> dict:
    return response.to_dict() if hasattr(response, "to_dict") else dict(response)


def confirmation_phrase(side: str, product_id: str, size: str) -> str:
    """The exact text a human must approve before a real order is sent."""
    return f"EXECUTE {side.upper()} {product_id} {size}"


class CoinbaseLiveConnector:
    def __init__(self, client: Any = None, max_quote_per_order: str = "10"):
        if client is None:
            from coinbase.rest import RESTClient

            # Reads COINBASE_API_KEY / COINBASE_API_SECRET from the environment.
            client = RESTClient()
        self._client = client
        self._max_quote = Decimal(max_quote_per_order)
        self.permissions = self._check_permissions()

    def _check_permissions(self) -> dict:
        perms = _as_dict(self._client.get_api_key_permissions())
        if not perms.get("can_view"):
            raise ConnectorError("API key cannot view the account.")
        if perms.get("can_transfer"):
            raise ConnectorError(
                "API key has transfer permission. Create a key with View + Trade only."
            )
        return perms

    # ---- read-only -------------------------------------------------------

    def get_real_balance(self) -> list[dict]:
        """All accounts of the key's portfolio, straight from Coinbase."""
        accounts: list[dict] = []
        cursor = None
        while True:
            page = _as_dict(self._client.get_accounts(limit=250, cursor=cursor))
            accounts.extend(page.get("accounts") or [])
            if not page.get("has_next"):
                return accounts
            cursor = page.get("cursor")

    def get_available_funds(self, currency: str) -> Decimal:
        """Spendable amount of one currency (funds held by open orders excluded)."""
        total = Decimal("0")
        for account in self.get_real_balance():
            if account.get("currency") == currency.upper():
                total += Decimal(account["available_balance"]["value"])
        return total

    def get_market_price(self, product_id: str) -> dict:
        books = _as_dict(self._client.get_best_bid_ask(product_ids=[product_id]))
        book = (books.get("pricebooks") or [None])[0]
        if not book or not book.get("bids") or not book.get("asks"):
            raise ConnectorError(f"No live order book for {product_id}.")
        bid = Decimal(book["bids"][0]["price"])
        ask = Decimal(book["asks"][0]["price"])
        return {
            "product_id": product_id,
            "bid": bid,
            "ask": ask,
            "mid": (bid + ask) / 2,
        }

    def get_product(self, product_id: str) -> dict:
        """Trading rules: minimum sizes, increments, status."""
        return _as_dict(
            self._client.get_product(product_id, get_tradability_status=True)
        )

    def preview_buy_order(self, product_id: str, quote_size: str) -> dict:
        return self._preview(
            self._client.preview_market_order_buy(product_id, quote_size=quote_size)
        )

    def preview_sell_order(self, product_id: str, base_size: str) -> dict:
        return self._preview(
            self._client.preview_market_order_sell(product_id, base_size=base_size)
        )

    @staticmethod
    def _preview(response: Any) -> dict:
        preview = _as_dict(response)
        if preview.get("errs"):
            raise ConnectorError(
                f"Coinbase rejected the order preview: {preview['errs']}"
            )
        return preview

    def get_real_order_status(self, order_id: str) -> dict:
        return _as_dict(self._client.get_order(order_id))["order"]

    def get_open_orders(self) -> list[dict]:
        """Resting orders of the key's portfolio."""
        return _as_dict(self._client.list_orders(order_status=["OPEN"])).get("orders") or []

    def find_order_by_client_id(self, client_order_id: str, limit: int = 100) -> dict | None:
        """Look an order up by the id WE chose. Used after a restart or a
        timeout to learn whether an order reached Coinbase. None = Coinbase
        does not list it among the most recent orders."""
        orders = _as_dict(self._client.list_orders(limit=limit)).get("orders") or []
        for order in orders:
            if order.get("client_order_id") == client_order_id:
                return order
        return None

    def get_real_fills(self, order_id: str) -> list[dict]:
        return _as_dict(self._client.get_fills(order_ids=[order_id])).get("fills") or []

    # ---- real money ------------------------------------------------------

    def execute_real_buy(
        self, product_id: str, quote_size: str, client_order_id: str, confirmation: str
    ) -> dict:
        self._require_approval("BUY", product_id, quote_size, confirmation)
        if Decimal(quote_size) > self._max_quote:
            raise LiveTradingBlocked(
                f"{quote_size} exceeds the per-order limit of {self._max_quote}."
            )
        if not self.permissions.get("can_trade"):
            raise ConnectorError("API key has no trade permission.")
        return self._created(
            self._client.market_order_buy(
                client_order_id, product_id, quote_size=quote_size
            )
        )

    def execute_real_sell(
        self, product_id: str, base_size: str, client_order_id: str, confirmation: str
    ) -> dict:
        self._require_approval("SELL", product_id, base_size, confirmation)
        notional = Decimal(base_size) * self.get_market_price(product_id)["bid"]
        if notional > self._max_quote:
            raise LiveTradingBlocked(
                f"Sell worth about {notional:.2f} exceeds the per-order limit "
                f"of {self._max_quote}."
            )
        if not self.permissions.get("can_trade"):
            raise ConnectorError("API key has no trade permission.")
        return self._created(
            self._client.market_order_sell(
                client_order_id, product_id, base_size=base_size
            )
        )

    def cancel_open_order(self, order_id: str) -> dict:
        results = _as_dict(self._client.cancel_orders([order_id])).get("results") or []
        if not results or not results[0].get("success"):
            raise ConnectorError(f"Cancel failed for {order_id}: {results}")
        return results[0]

    @staticmethod
    def _require_approval(
        side: str, product_id: str, size: str, confirmation: str
    ) -> None:
        if os.environ.get(LIVE_FLAG) != "1":
            raise LiveTradingBlocked(f"{LIVE_FLAG} is not set to 1. No order was sent.")
        if confirmation != confirmation_phrase(side, product_id, size):
            raise LiveTradingBlocked(
                "Confirmation does not match the order exactly. No order was sent."
            )

    @staticmethod
    def _created(response: Any) -> dict:
        created = _as_dict(response)
        if not created.get("success"):
            raise ConnectorError(
                f"Coinbase rejected the order: {created.get('error_response')}"
            )
        # Accepted by Coinbase, not yet proven filled: read status and fills back.
        return created["success_response"]
