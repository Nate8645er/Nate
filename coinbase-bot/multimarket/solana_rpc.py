"""Real Solana on-chain checks via the free public RPC (no key).

Fills the OnChain risk inputs from live chain data: mint/freeze authority,
Token-2022 program, supply, and top-holder concentration. Any field that
cannot be fetched stays None -> the risk engine reports UNKNOWN, never SAFE.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.request
from typing import Optional

from .core import OnChain

PUBLIC_RPC = "https://api.mainnet-beta.solana.com"
SPL_TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
_CA = "/root/.ccr/ca-bundle.crt"
_UA = "hypergrok-research/1.0"


def _ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        if os.path.exists(_CA):
            ctx.load_verify_locations(_CA)
    except Exception:
        pass
    return ctx


def rpc_call(method: str, params: list, endpoint: str = PUBLIC_RPC, timeout: int = 20):
    """One JSON-RPC call. Returns the `result` object or None on any error."""
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    try:
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers={"content-type": "application/json", "user-agent": _UA},
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as resp:
            return json.loads(resp.read().decode("utf-8")).get("result")
    except Exception:
        return None


def rpc_alive(endpoint: str = PUBLIC_RPC) -> bool:
    return rpc_call("getVersion", [], endpoint) is not None


def parse_mint_account(result: Optional[dict]) -> dict:
    """Extract authority / program / supply from a getAccountInfo(jsonParsed)
    result. Unknown fields stay None."""
    out = {
        "mint_authority_active": None,
        "freeze_authority_active": None,
        "is_token_2022": None,
        "decimals": None,
        "supply": None,
    }
    if not isinstance(result, dict):
        return out
    value = result.get("value") or {}
    owner = value.get("owner")
    if owner in (SPL_TOKEN, TOKEN_2022):
        out["is_token_2022"] = owner == TOKEN_2022
    info = (((value.get("data") or {}).get("parsed") or {}).get("info")) or {}
    if "mintAuthority" in info:
        out["mint_authority_active"] = info["mintAuthority"] is not None
    if "freezeAuthority" in info:
        out["freeze_authority_active"] = info["freezeAuthority"] is not None
    if info.get("decimals") is not None:
        out["decimals"] = info["decimals"]
    supply = info.get("supply")
    if supply is not None and info.get("decimals") is not None:
        try:
            out["supply"] = int(supply) / (10 ** int(info["decimals"]))
        except (TypeError, ValueError):
            pass
    return out


def top_holder_pct(
    largest: Optional[dict], supply_ui: Optional[float]
) -> Optional[float]:
    """Largest single token account as a % of supply, from getTokenLargestAccounts."""
    if not isinstance(largest, dict) or not supply_ui:
        return None
    vals = largest.get("value") or []
    if not vals:
        return None
    top = vals[0].get("uiAmount")
    if top is None:
        return None
    try:
        return float(top) / float(supply_ui) * 100
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def fetch_onchain(mint_address: str, endpoint: str = PUBLIC_RPC) -> OnChain:
    """Build an OnChain record from live RPC data. Missing data stays None."""
    acct = rpc_call(
        "getAccountInfo", [mint_address, {"encoding": "jsonParsed"}], endpoint
    )
    parsed = parse_mint_account(acct)
    supply_res = rpc_call("getTokenSupply", [mint_address], endpoint)
    supply_ui = None
    if isinstance(supply_res, dict):
        supply_ui = (supply_res.get("value") or {}).get("uiAmount")
    largest = rpc_call("getTokenLargestAccounts", [mint_address], endpoint)
    conc = top_holder_pct(largest, supply_ui)
    return OnChain(
        mint_authority_active=parsed["mint_authority_active"],
        freeze_authority_active=parsed["freeze_authority_active"],
        token2022_transfer_fee=(
            parsed["is_token_2022"] if parsed["is_token_2022"] else None
        ),
        top_holder_pct=conc,
    )
