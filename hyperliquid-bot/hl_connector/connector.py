"""Hyperliquid spot connector (mainnet, official hyperliquid-python-sdk).

Every method talks to the real Hyperliquid API. There is no paper mode and no
simulated balance: if a call fails, it raises.

Safety rules enforced here:
  * Spot pairs only. Perpetuals cannot be addressed through this connector,
    and it contains no transfer or withdrawal call at all.
  * Real orders need HL_LIVE_TRADING_ENABLED=1, no kill switch, a confirmation
    string that repeats the exact prepared order, and a size within the
    per-order capital limit.
  * Every order carries a client order id (cloid) that is journaled before it
    is sent. A cloid that was already submitted is refused, so a retry cannot
    create a second order.
  * The API wallet key is read from the environment, held only as a signer
    object, and never printed or logged.
  * A submitted order is NOT proof of a fill. Read it back with
    get_order_status() and get_order_fills().
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any

LIVE_FLAG = "HL_LIVE_TRADING_ENABLED"
KEY_VAR = "HL_API_WALLET_KEY"
ADDRESS_VAR = "HL_MAIN_WALLET_ADDRESS"
MIN_ORDER_USDC = Decimal("10")  # documented Hyperliquid minimum order value
SPOT_ASSET_OFFSET = 10000
IOC = {"limit": {"tif": "Ioc"}}


class ConnectorError(RuntimeError):
    """Hyperliquid rejected a request or returned something unusable."""


class LiveTradingBlocked(ConnectorError):
    """A real order was requested without the required approval."""


def load_env_file(path: str | Path) -> None:
    """Load NAME=value lines into the environment without overriding it."""
    file = Path(path)
    if not file.exists():
        return
    for line in file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            if value.strip():
                os.environ.setdefault(name.strip(), value.strip().strip("'\""))


def confirmation_phrase(order: dict) -> str:
    """The exact text a human must approve before this order is sent."""
    return f"EXECUTE {order['side']} {order['pair']} {order['size']} LIMIT {order['limit_px']}"


def _floor(value: Decimal, decimals: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_DOWN)


def _round_price(price: Decimal, sz_decimals: int) -> Decimal:
    # Hyperliquid spot prices: at most 5 significant figures and
    # at most (8 - szDecimals) decimal places.
    return Decimal(str(round(float(f"{float(price):.5g}"), 8 - sz_decimals)))


class HyperliquidSpotConnector:
    def __init__(
        self,
        main_address: str | None = None,
        info: Any = None,
        exchange: Any = None,
        wallet: Any = None,
        max_usdc_per_order: str = "15",
        state_dir: str | Path | None = None,
    ):
        self.main_address = main_address or os.environ.get(ADDRESS_VAR)
        if not self.main_address:
            raise ConnectorError(f"{ADDRESS_VAR} is not set.")
        if info is None:
            from hyperliquid.info import Info
            from hyperliquid.utils import constants

            info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self._info = info
        self._exchange = exchange
        self._wallet = wallet if wallet is not None else self._wallet_from_env()
        self._max_usdc = Decimal(max_usdc_per_order)
        self._state = Path(
            state_dir or Path(__file__).resolve().parent.parent / "state"
        )
        self._market_cache: dict[str, dict] | None = None

    @staticmethod
    def _wallet_from_env() -> Any:
        key = os.environ.get(KEY_VAR)
        if not key:
            return None
        from eth_account import Account

        try:
            return Account.from_key(key)
        except Exception:
            # Never echo the value: the message must not contain the key.
            raise ConnectorError(f"{KEY_VAR} is not a valid private key.") from None

    # ---- read-only -------------------------------------------------------

    def account_exists(self) -> bool:
        role = self._info.post("/info", {"type": "userRole", "user": self.main_address})
        return role.get("role") != "missing"

    def api_wallet_address(self) -> str | None:
        return self._wallet.address if self._wallet else None

    def api_wallet_authorized(self) -> bool:
        """True only if Hyperliquid lists the API wallet as agent of the main wallet."""
        if not self._wallet:
            return False
        role = self._info.post(
            "/info", {"type": "userRole", "user": self._wallet.address}
        )
        owner = (role.get("data") or {}).get("user", "")
        return (
            role.get("role") == "agent" and owner.lower() == self.main_address.lower()
        )

    def get_real_balance(self) -> list[dict]:
        """Spot balances of the main wallet, straight from Hyperliquid."""
        return self._info.spot_user_state(self.main_address).get("balances") or []

    def get_available(self, token: str) -> Decimal:
        for balance in self.get_real_balance():
            if balance["coin"] == token:
                return Decimal(balance["total"]) - Decimal(balance["hold"])
        return Decimal("0")

    def get_spot_markets(self) -> dict[str, dict]:
        """All spot pairs keyed as BASE/QUOTE."""
        if self._market_cache is None:
            meta = self._info.spot_meta()
            tokens = {token["index"]: token for token in meta["tokens"]}
            markets = {}
            for pair in meta["universe"]:
                base, quote = (tokens[index] for index in pair["tokens"])
                markets[f"{base['name']}/{quote['name']}"] = {
                    "name": pair["name"],
                    "asset": SPOT_ASSET_OFFSET + pair["index"],
                    "base": base["name"],
                    "quote": quote["name"],
                    "sz_decimals": base["szDecimals"],
                }
            self._market_cache = markets
        return self._market_cache

    def _market(self, pair: str) -> dict:
        market = self.get_spot_markets().get(pair)
        if market is None:
            raise ConnectorError(f"{pair} is not a Hyperliquid spot pair. Spot only.")
        return market

    def get_market_price(self, pair: str) -> dict:
        levels = self._info.l2_snapshot(self._market(pair)["name"])["levels"]
        if not levels[0] or not levels[1]:
            raise ConnectorError(f"No live order book for {pair}.")
        bid, ask = Decimal(levels[0][0]["px"]), Decimal(levels[1][0]["px"])
        return {"pair": pair, "bid": bid, "ask": ask, "mid": (bid + ask) / 2}

    def get_taker_fee_rate(self) -> Decimal:
        return Decimal(self._info.user_fees(self.main_address)["userSpotCrossRate"])

    def get_order_status(self, oid: int) -> dict:
        return self._info.query_order_by_oid(self.main_address, oid)

    def get_order_fills(self, oid: int) -> list[dict]:
        return [
            fill
            for fill in self._info.user_fills(self.main_address)
            if fill["oid"] == oid
        ]

    # ---- prepare and sign (nothing is sent) ------------------------------

    def prepare_buy_order(
        self,
        pair: str,
        usdc_amount: str,
        slippage: str = "0.01",
        check_funds: bool = True,
    ) -> dict:
        market = self._market(pair)
        ask = self.get_market_price(pair)["ask"]
        size = _floor(Decimal(usdc_amount) / ask, market["sz_decimals"])
        limit = _round_price(ask * (1 + Decimal(slippage)), market["sz_decimals"])
        return self._prepared("BUY", pair, market, size, limit, ask, check_funds)

    def prepare_sell_order(
        self,
        pair: str,
        base_size: str,
        slippage: str = "0.01",
        check_funds: bool = True,
    ) -> dict:
        market = self._market(pair)
        bid = self.get_market_price(pair)["bid"]
        size = _floor(Decimal(base_size), market["sz_decimals"])
        limit = _round_price(bid * (1 - Decimal(slippage)), market["sz_decimals"])
        return self._prepared("SELL", pair, market, size, limit, bid, check_funds)

    def _prepared(self, side, pair, market, size, limit, price, check_funds) -> dict:
        notional = size * price
        if notional < MIN_ORDER_USDC:
            raise ConnectorError(
                f"Order value {notional:.2f} is below the minimum of {MIN_ORDER_USDC} USDC."
            )
        order = {
            "side": side,
            "pair": pair,
            "name": market["name"],
            "asset": market["asset"],
            "size": str(size),
            "limit_px": str(limit),
            "est_price": str(price),
            "est_notional": str(notional),
            "est_fee": str(notional * self.get_taker_fee_rate()),
            "cloid": "0x" + secrets.token_hex(16),
        }
        if check_funds:
            self._require_funds(order, market)
        order["confirmation"] = confirmation_phrase(order)
        return order

    def _require_funds(self, order: dict, market: dict) -> None:
        if order["side"] == "BUY":
            token, needed = market["quote"], Decimal(order["size"]) * Decimal(
                order["limit_px"]
            )
        else:
            token, needed = market["base"], Decimal(order["size"])
        available = self.get_available(token)
        if available < needed:
            raise ConnectorError(
                f"Insufficient {token}: need {needed}, available {available}."
            )

    def sign_order(self, order: dict) -> dict:
        """Sign the order locally with the API wallet. Nothing is sent."""
        if not self._wallet:
            raise ConnectorError(f"{KEY_VAR} is not set.")
        from hyperliquid.utils.signing import (
            get_timestamp_ms,
            order_request_to_order_wire,
            order_wires_to_order_action,
            sign_l1_action,
        )
        from hyperliquid.utils.types import Cloid

        self._require_spot(order)
        request = {
            "coin": order["name"],
            "is_buy": order["side"] == "BUY",
            "sz": float(order["size"]),
            "limit_px": float(order["limit_px"]),
            "order_type": IOC,
            "reduce_only": False,
            "cloid": Cloid.from_str(order["cloid"]),
        }
        action = order_wires_to_order_action(
            [order_request_to_order_wire(request, order["asset"])]
        )
        nonce = get_timestamp_ms()
        signature = sign_l1_action(self._wallet, action, None, nonce, None, True)
        return {
            "action": action,
            "nonce": nonce,
            "signature": signature,
            "signer": self._wallet.address,
        }

    # ---- real money ------------------------------------------------------

    def execute_real_buy(self, order: dict, confirmation: str) -> dict:
        return self._execute("BUY", order, confirmation)

    def execute_real_sell(self, order: dict, confirmation: str) -> dict:
        return self._execute("SELL", order, confirmation)

    def cancel_order(self, pair: str, oid: int) -> dict:
        response = self._exchange_client().cancel(self._market(pair)["name"], oid)
        status = self._first_status(response)
        self._journal("cancelled", {"pair": pair, "oid": oid})
        return {"status": status}

    def emergency_stop(self, reason: str = "manual") -> None:
        """Kill switch: blocks every further real order until the file is removed."""
        self._state.mkdir(parents=True, exist_ok=True)
        (self._state / "KILL_SWITCH").write_text(reason + "\n")
        self._journal("kill_switch", {"reason": reason})

    def _execute(self, side: str, order: dict, confirmation: str) -> dict:
        if (self._state / "KILL_SWITCH").exists():
            raise LiveTradingBlocked("Kill switch is active. No order was sent.")
        if os.environ.get(LIVE_FLAG) != "1":
            raise LiveTradingBlocked(f"{LIVE_FLAG} is not set to 1. No order was sent.")
        if order["side"] != side or confirmation != confirmation_phrase(order):
            raise LiveTradingBlocked(
                "Confirmation does not match the order exactly. No order was sent."
            )
        self._require_spot(order)
        if Decimal(order["size"]) * Decimal(order["limit_px"]) > self._max_usdc:
            raise LiveTradingBlocked(
                f"Order exceeds the per-order limit of {self._max_usdc} USDC. No order was sent."
            )
        if order["cloid"] in self._submitted_cloids():
            raise LiveTradingBlocked(
                "This order was already submitted once. No second order was sent."
            )
        self._require_funds(order, self._market(order["pair"]))
        exchange = self._exchange_client()

        from hyperliquid.utils.types import Cloid

        # Journal first: after a crash the cloid is known and cannot be re-sent.
        self._journal("submitted", order)
        response = exchange.order(
            order["name"],
            side == "BUY",
            float(order["size"]),
            float(order["limit_px"]),
            IOC,
            cloid=Cloid.from_str(order["cloid"]),
        )
        status = self._first_status(response)
        self._journal("accepted", {"cloid": order["cloid"], "status": status})
        return status

    def _require_spot(self, order: dict) -> None:
        market = self.get_spot_markets().get(order["pair"])
        if (
            market is None
            or market["asset"] != order["asset"]
            or market["name"] != order["name"]
            or order["asset"] < SPOT_ASSET_OFFSET
        ):
            raise LiveTradingBlocked(
                "Order is not a known spot pair. No order was sent."
            )

    def _exchange_client(self) -> Any:
        if self._exchange is None:
            if not self._wallet:
                raise ConnectorError(f"{KEY_VAR} is not set.")
            from hyperliquid.exchange import Exchange
            from hyperliquid.utils import constants

            self._exchange = Exchange(
                self._wallet,
                constants.MAINNET_API_URL,
                account_address=self.main_address,
            )
        return self._exchange

    @staticmethod
    def _first_status(response: dict) -> Any:
        if response.get("status") != "ok":
            raise ConnectorError(
                f"Hyperliquid rejected the request: {response.get('response')}"
            )
        status = response["response"]["data"]["statuses"][0]
        if isinstance(status, dict) and "error" in status:
            raise ConnectorError(f"Hyperliquid rejected the order: {status['error']}")
        return status

    # ---- journal ---------------------------------------------------------

    def _journal(self, event: str, data: dict) -> None:
        self._state.mkdir(parents=True, exist_ok=True)
        entry = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **data}
        with (self._state / "orders.jsonl").open("a") as file:
            file.write(json.dumps(entry) + "\n")

    def _submitted_cloids(self) -> set[str]:
        journal = self._state / "orders.jsonl"
        if not journal.exists():
            return set()
        entries = (
            json.loads(line) for line in journal.read_text().splitlines() if line
        )
        return {entry["cloid"] for entry in entries if entry["event"] == "submitted"}
