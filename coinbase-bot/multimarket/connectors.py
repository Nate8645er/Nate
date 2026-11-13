"""Live connector status checks. Each returns CONNECTED / NOT CONNECTED based
on a real reachability probe of a free endpoint. Phantom is a wallet, not a
data endpoint, and no wallet is connected (no keys) -> always NOT CONNECTED."""

from __future__ import annotations

from . import jupiter, solana_rpc
from .discovery import safe_get_json

CONNECTED = "CONNECTED"
NOT_CONNECTED = "NOT CONNECTED"
ERROR = "ERROR"


def _coinbase() -> str:
    data = safe_get_json("https://api.exchange.coinbase.com/products/BTC-USD/ticker")
    return CONNECTED if isinstance(data, dict) and data.get("price") else NOT_CONNECTED


def _geckoterminal() -> str:
    data = safe_get_json(
        "https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1"
    )
    return CONNECTED if isinstance(data, dict) and data.get("data") else NOT_CONNECTED


def _dexscreener() -> str:
    data = safe_get_json("https://api.dexscreener.com/token-profiles/latest/v1")
    return CONNECTED if isinstance(data, list) else NOT_CONNECTED


def check_connectors() -> list:
    """Probe every data source once. Returns [{name, status, detail}]."""
    probes = {
        "Coinbase": _coinbase,
        "Solana RPC": lambda: CONNECTED if solana_rpc.rpc_alive() else NOT_CONNECTED,
        "Jupiter": lambda: CONNECTED if jupiter.alive() else NOT_CONNECTED,
        "GeckoTerminal": _geckoterminal,
        "DexScreener": _dexscreener,
    }
    out = []
    for name, probe in probes.items():
        try:
            status = probe()
        except Exception:
            status = ERROR
        out.append({"name": name, "status": status, "detail": "free/public"})
    out.append(
        {
            "name": "Phantom",
            "status": NOT_CONNECTED,
            "detail": "Wallet — bewusst nicht verbunden (keine Keys, keine Signatur)",
        }
    )
    return out
