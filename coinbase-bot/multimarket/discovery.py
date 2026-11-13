"""New-token discovery from free, public data sources.

Real HTTP (standard library urllib) through the environment proxy, trusting the
agent CA bundle when present. On any failure it returns an empty list and the
caller documents the gap — it never fabricates tokens. No API key required for
GeckoTerminal or DexScreener public endpoints.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.request
from typing import Optional

from .core import Token, categorize_market_cap

_CA = "/root/.ccr/ca-bundle.crt"
_UA = "hypergrok-research/1.0 (+contact-on-request)"  # generic, no personal data


def _ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        if os.path.exists(_CA):
            ctx.load_verify_locations(_CA)
    except Exception:
        pass
    return ctx


def safe_get_json(url: str, timeout: int = 20) -> Optional[object]:
    """GET + parse JSON. Returns None on any error (never raises to caller)."""
    try:
        req = urllib.request.Request(
            url, headers={"accept": "application/json", "user-agent": _UA}
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _num(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


class GeckoTerminalSource:
    """GeckoTerminal public API: new pools per network (free, no key)."""

    BASE = "https://api.geckoterminal.com/api/v2"

    def __init__(self, network: str = "solana"):
        self.network = network

    def new_pools(self, pages: int = 1) -> list[Token]:
        tokens: list[Token] = []
        for page in range(1, pages + 1):
            data = safe_get_json(
                f"{self.BASE}/networks/{self.network}/new_pools?page={page}"
            )
            if not isinstance(data, dict):
                break
            for pool in data.get("data", []):
                a = pool.get("attributes", {})
                rel = (
                    pool.get("relationships", {}).get("base_token", {}).get("data", {})
                )
                base_id = rel.get("id", "")  # e.g. "solana_<address>"
                address = base_id.split("_", 1)[1] if "_" in base_id else base_id
                vol = a.get("volume_usd", {}) or {}
                txns = (a.get("transactions", {}) or {}).get("h24", {}) or {}
                tokens.append(
                    Token(
                        address=address,
                        symbol=(a.get("name", "") or "").split(" / ")[0][:20],
                        name=a.get("name", ""),
                        network=self.network,
                        source="geckoterminal",
                        created_at=a.get("pool_created_at"),
                        price_usd=_num(a.get("base_token_price_usd")),
                        market_cap_usd=_num(a.get("market_cap_usd")),
                        fdv_usd=_num(a.get("fdv_usd")),
                        liquidity_usd=_num(a.get("reserve_in_usd")),
                        volume_24h_usd=_num(vol.get("h24")),
                        buyers_24h=txns.get("buyers"),
                        sellers_24h=txns.get("sellers"),
                        trades_24h=(txns.get("buys") or 0) + (txns.get("sells") or 0)
                        or None,
                        price_change_24h_pct=_num(
                            (a.get("price_change_percentage", {}) or {}).get("h24")
                        ),
                        pool_address=a.get("address"),
                    )
                )
        return tokens


class DexScreenerSource:
    """DexScreener public API: latest token profiles (free, no key). Profiles
    are address-only; market data is left None (honest) unless enriched."""

    BASE = "https://api.dexscreener.com"

    def latest_profiles(self, chain: str = "solana", limit: int = 30) -> list[Token]:
        data = safe_get_json(f"{self.BASE}/token-profiles/latest/v1")
        if not isinstance(data, list):
            return []
        out: list[Token] = []
        for p in data:
            if p.get("chainId") != chain:
                continue
            out.append(
                Token(
                    address=p.get("tokenAddress", ""),
                    symbol="",
                    name="",
                    network=chain,
                    source="dexscreener",
                )
            )
            if len(out) >= limit:
                break
        return out


class TokenScanner:
    """Merges sources, removes duplicates and categorises by market cap."""

    def __init__(self, sources: list):
        self.sources = sources

    def scan(self) -> list[dict]:
        seen: set = set()
        results: list[dict] = []
        for source in self.sources:
            tokens = (
                source.new_pools()
                if hasattr(source, "new_pools")
                else source.latest_profiles()
            )
            for token in tokens:
                key = token.dedup_key()
                if not token.address or key in seen:
                    continue
                seen.add(key)
                results.append(
                    {
                        "token": token,
                        "category": categorize_market_cap(
                            token.market_cap_usd or token.fdv_usd
                        ),
                    }
                )
        return results
