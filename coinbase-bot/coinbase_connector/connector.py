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
    def __init__(
        self,
        client: Any = None,
        max_quote_per_order: str = "10",
        credentials: dict | None = None,
    ):
        """``credentials`` (``{"api_key", "api_secret"}``) are passed to the SDK
        in memory and never stored; use ``coinbase_connector.keyfile`` to load
        them from a file the operator keeps outside the repository. With no
        client and no credentials, the SDK reads the key from the environment.
        A transfer-capable key is refused in ``_check_permissions``."""
        if client is None:
            from coinbase.rest import RESTClient

            if credentials:
                client = RESTClient(
                    api_key=credentials["api_key"], api_secret=credentials["api_secret"]
                )
            else:
                # Reads the key from the environment (COINBASE_API_KEY / ...).
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

    def get_available_funds(
        self, currency: str, portfolio_only: bool = True
    ) -> Decimal:
        """Spendable amount of one currency (funds held by open orders excluded).

        Per the spec, each Account carries ``retail_portfolio_id``; with
        ``portfolio_only`` (the default) only accounts belonging to the key's
        own portfolio are counted, so funds in any other portfolio are never
        treated as spendable - a second guard on portfolio isolation beyond the
        key's own ``portfolio_uuid``."""
        own = self.permissions.get("portfolio_uuid")
        total = Decimal("0")
        for account in self.get_real_balance():
            if account.get("currency") != currency.upper():
                continue
            if (
                portfolio_only
                and own
                and account.get("retail_portfolio_id") not in (own, None)
            ):
                continue
            total += Decimal(account["available_balance"]["value"])
        return total

    def assert_portfolio_isolation(self) -> dict:
        """Prove the key can only see its own portfolio. Reads every account
        (spec field ``retail_portfolio_id``) and confirms none belongs to a
        different portfolio than the key's ``portfolio_uuid``. Raises on any
        foreign account; returns a summary otherwise. Read-only."""
        own = self.permissions.get("portfolio_uuid")
        if not own:
            raise ConnectorError(
                "API key reports no portfolio_uuid; isolation unverifiable."
            )
        foreign, seen = [], set()
        for account in self.get_real_balance():
            pid = account.get("retail_portfolio_id")
            if pid is not None:
                seen.add(pid)
                if pid != own:
                    foreign.append(
                        {"currency": account.get("currency"), "portfolio": pid}
                    )
        if foreign:
            raise ConnectorError(f"Key sees foreign-portfolio accounts: {foreign}")
        return {
            "portfolio_uuid": own,
            "portfolios_seen": sorted(seen),
            "cannot_transfer": not self.permissions.get("can_transfer"),
        }

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
    def preview_metrics(preview: dict) -> dict:
        """Coinbase's own figures from an OrderPreviewResponse (spec fields):
        order_total, commission_total, slippage (percent), best_bid, best_ask.
        Missing fields come back as None - never guessed. These are more exact
        than approximating slippage/fees from a separate quote."""

        def dec(key):
            v = preview.get(key)
            try:
                return Decimal(str(v)) if v is not None and v != "" else None
            except Exception:  # noqa: BLE001
                return None

        return {
            "order_total": dec("order_total"),
            "commission_total": dec("commission_total"),
            "slippage_pct": dec("slippage"),
            "best_bid": dec("best_bid"),
            "best_ask": dec("best_ask"),
            "preview_id": preview.get("preview_id"),
        }

    @staticmethod
    def error_detail(exc: Exception) -> dict:
        """Best-effort extraction of the spec error shape {error, code, message,
        details} from an SDK exception, for logging. Never raises."""
        out = {"type": type(exc).__name__, "text": str(exc)[:300]}
        body = getattr(exc, "response", None)
        for attr in ("error", "code", "message"):
            val = getattr(exc, attr, None)
            if val is not None:
                out[attr] = val
        if isinstance(body, dict):
            for k in ("error", "code", "message"):
                if k in body:
                    out[k] = body[k]
        return out

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

    def _portfolio_scope(self) -> dict:
        """Spec: list_orders and fills accept ``retail_portfolio_id``. Scope
        every order/fill query to the key's own portfolio."""
        own = self.permissions.get("portfolio_uuid")
        return {"retail_portfolio_id": own} if own else {}

    def _paged_orders(self, max_pages: int = 10, **params) -> list[dict]:
        """Follow the spec's ``cursor`` / ``has_next`` pagination."""
        orders: list[dict] = []
        cursor = None
        for _ in range(max_pages):
            page = _as_dict(
                self._client.list_orders(
                    cursor=cursor, **self._portfolio_scope(), **params
                )
            )
            orders.extend(page.get("orders") or [])
            cursor = page.get("cursor")
            if not page.get("has_next") or not cursor:
                break
        return orders

    def get_open_orders(self) -> list[dict]:
        """Resting orders of the key's own portfolio (all pages)."""
        return self._paged_orders(order_status=["OPEN"])

    def find_order_by_client_id(
        self, client_order_id: str, limit: int = 100, max_pages: int = 10
    ) -> dict | None:
        """Look an order up by the id WE chose. Used after a restart or a
        timeout to learn whether an order reached Coinbase. Searches the own
        portfolio across up to ``max_pages`` pages. None = not found there."""
        for order in self._paged_orders(max_pages=max_pages, limit=limit):
            if order.get("client_order_id") == client_order_id:
                return order
        return None

    def get_real_fills(self, order_id: str) -> list[dict]:
        """All fills of one order (spec: Fill.price, size, commission)."""
        fills: list[dict] = []
        cursor = None
        for _ in range(10):
            page = _as_dict(
                self._client.get_fills(
                    order_ids=[order_id], cursor=cursor, **self._portfolio_scope()
                )
            )
            fills.extend(page.get("fills") or [])
            cursor = page.get("cursor")
            if not cursor:
                break
        return fills

    def reconcile_fills(self, order_id: str) -> dict:
        """Cross-check an order against its fills (spec fields). The order's
        filled_size and total_fees must equal the sum over its fills; a
        mismatch is reported, never silently accepted."""
        order = self.get_real_order_status(order_id)
        fills = self.get_real_fills(order_id)

        def base_size(f):
            # Spec Fill.size_in_quote: a quote-sized order (e.g. a USDC-amount
            # market buy) reports fill size in QUOTE currency. Convert with the
            # fill price; summing raw sizes would mix USDC and BTC.
            raw = Decimal(str(f.get("size") or "0"))
            if f.get("size_in_quote") in (True, "true", "True"):
                price = Decimal(str(f.get("price") or "0"))
                return raw / price if price > 0 else Decimal("0")
            return raw

        size = sum((base_size(f) for f in fills), Decimal("0"))
        fees = sum(
            (Decimal(str(f.get("commission") or "0")) for f in fills), Decimal("0")
        )
        o_size = Decimal(str(order.get("filled_size") or "0"))
        o_fees = Decimal(str(order.get("total_fees") or "0"))
        tol = Decimal("0.00000001")
        return {
            "order_id": order_id,
            "status": order.get("status"),
            "fills": len(fills),
            "fill_size": str(size),
            "order_filled_size": str(o_size),
            "fill_fees": str(fees),
            "order_total_fees": str(o_fees),
            "match": abs(size - o_size) <= tol
            and abs(fees - o_fees) <= Decimal("0.000001"),
        }

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

    # ---- limit exits -----------------------------------------------------
    # The SDK exposes market, limit (GTC/GTD/IOC/FOK), stop-limit and
    # trigger-bracket orders. We use a market exit by default (certain to
    # flatten) and a GTC limit exit when a worse-than-limit fill must be
    # avoided. NONE of these guarantees an execution price; see
    # supported_order_types().

    def preview_limit_sell(
        self, product_id: str, base_size: str, limit_price: str
    ) -> dict:
        return self._preview(
            self._client.preview_limit_order_gtc_sell(
                product_id, base_size=base_size, limit_price=limit_price
            )
        )

    def execute_real_limit_sell(
        self,
        product_id: str,
        base_size: str,
        limit_price: str,
        client_order_id: str,
        confirmation: str,
    ) -> dict:
        self._require_approval("SELL", product_id, base_size, confirmation)
        if not self.permissions.get("can_trade"):
            raise ConnectorError("API key has no trade permission.")
        return self._created(
            self._client.limit_order_gtc_sell(
                client_order_id,
                product_id,
                base_size=base_size,
                limit_price=limit_price,
            )
        )

    @staticmethod
    def supported_order_types() -> dict:
        """What Coinbase Advanced Trade really offers for spot, and the honest
        guarantee of each. A stop order is a trigger to SEND an order, not a
        promise about the fill price: in a fast move the market can gap through
        the stop and fill worse, and a stop-LIMIT can fail to fill at all."""
        return {
            "market": "fills immediately at the best available price; no price guarantee",
            "limit_gtc": "rests until filled or cancelled; fills only at the limit or better",
            "limit_gtd": "limit with an expiry time",
            "limit_ioc/fok": "fill now or cancel (partial / all-or-none)",
            "stop_limit": "trigger places a LIMIT order; may NOT fill if price gaps past it",
            "trigger_bracket": "take-profit + stop-loss bracket; same no-guarantee caveat",
            "guarantee": "NO order type guarantees a maximum loss or an exact fill price.",
        }

    def verify_access(
        self,
        expected_portfolio_id: str | None = None,
        products: tuple = ("BTC-USDC", "ETH-USDC", "SOL-USDC"),
    ) -> dict:
        """Read-only check of everything Phase 16 section 3 lists. Sends no
        order. Every field is read from Coinbase; a failure is reported, never
        guessed."""
        report: dict = {"ok": False, "checks": {}, "errors": []}

        def step(name, fn):
            try:
                report["checks"][name] = fn()
            except Exception as exc:  # noqa: BLE001
                report["errors"].append(f"{name}: {type(exc).__name__}: {exc}")
                report["checks"][name] = None

        perms = self.permissions
        report["checks"]["permissions"] = {
            "can_view": perms.get("can_view"),
            "can_trade": perms.get("can_trade"),
            "can_transfer": perms.get("can_transfer"),
            "portfolio_uuid": perms.get("portfolio_uuid"),
        }
        step("balance_usdc", lambda: str(self.get_available_funds("USDC")))
        step(
            "tradable_products",
            lambda: {
                p: _as_dict(
                    self._client.get_product(p, get_tradability_status=True)
                ).get("status")
                for p in products
            },
        )
        step("open_orders", lambda: len(self.get_open_orders()))
        step(
            "order_history",
            lambda: len(
                _as_dict(
                    self._client.list_orders(limit=25, **self._portfolio_scope())
                ).get("orders")
                or []
            ),
        )
        step(
            "fees",
            lambda: _as_dict(self._client.get_transaction_summary()).get("fee_tier"),
        )
        portfolio = perms.get("portfolio_uuid")
        isolated = bool(portfolio) and (
            expected_portfolio_id is None or portfolio == expected_portfolio_id
        )
        # Second, stronger proof: no account belongs to a foreign portfolio
        # (spec field Account.retail_portfolio_id).
        try:
            report["checks"]["isolation_proof"] = self.assert_portfolio_isolation()
        except Exception as exc:  # noqa: BLE001
            report["errors"].append(f"isolation: {type(exc).__name__}: {exc}")
            report["checks"]["isolation_proof"] = None
            isolated = False
        report["checks"]["portfolio_isolated"] = isolated
        report["checks"]["cannot_transfer"] = not perms.get("can_transfer")
        report["ok"] = (
            bool(perms.get("can_view"))
            and bool(perms.get("can_trade"))
            and not perms.get("can_transfer")
            and isolated
            and not report["errors"]
        )
        return report

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
