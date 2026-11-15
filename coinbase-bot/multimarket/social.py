"""Social / Attention (workstation 08) — free, authorised public sources only.

What is real here:
  * CoinGecko's public `search/trending` endpoint: which assets people are
    actually looking up right now (an attention signal, measured by CoinGecko),
  * DexScreener token profiles: whether a token publishes social links at all
    (a token with no website and no socials is a different animal from one
    with a public presence).

Deliberately NOT done:
  * no scraping of X/Twitter, Telegram or Discord, and no bypassing of any
    access restriction,
  * no sentiment score is invented. CryptoPanic and comparable news APIs
    answer 403 without a paid key from here, so "sentiment" is reported as
    UNAVAILABLE_NO_FREE_SOURCE. Attention is not the same as sentiment and is
    labelled as attention.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from .discovery import safe_get_json

TRENDING = "https://api.coingecko.com/api/v3/search/trending"
PROFILES = "https://api.dexscreener.com/token-profiles/latest/v1"
NO_SENTIMENT = "UNAVAILABLE_NO_FREE_SOURCE"


@dataclass
class AttentionReport:
    trending: list                 # [{name, symbol, rank, score}]
    source: str
    available: bool
    sentiment_score: str           # always UNAVAILABLE_NO_FREE_SOURCE
    notes: list

    def to_dict(self) -> dict:
        return asdict(self)


def trending_assets(limit: int = 10) -> AttentionReport:
    data = safe_get_json(TRENDING)
    notes = ["Aufmerksamkeit != Stimmung. Es wird kein Sentiment-Wert geschaetzt.",
             "Kein Scraping, keine Umgehung von Zugriffssperren."]
    if not isinstance(data, dict) or "coins" not in data:
        notes.append("CoinGecko-Trending nicht erreichbar.")
        return AttentionReport([], "coingecko", False, NO_SENTIMENT, notes)
    rows = []
    for entry in (data.get("coins") or [])[:limit]:
        item = entry.get("item") or {}
        rows.append({
            "name": item.get("name"),
            "symbol": (item.get("symbol") or "").upper(),
            "rank": item.get("market_cap_rank"),
            "score": item.get("score"),
        })
    return AttentionReport(rows, "coingecko/search/trending", True, NO_SENTIMENT, notes)


def social_presence(token_address: str, chain: str = "solana") -> dict:
    """Does the token publish any public links at all? Real metadata, not a score."""
    data = safe_get_json(PROFILES)
    if not isinstance(data, list):
        return {"available": False, "reason": "DexScreener-Profile nicht erreichbar"}
    for p in data:
        if p.get("chainId") == chain and (p.get("tokenAddress") or "").lower() == token_address.lower():
            links = p.get("links") or []
            return {"available": True, "has_profile": True,
                    "link_count": len(links),
                    "types": sorted({(l.get("type") or l.get("label") or "link") for l in links}),
                    "has_description": bool(p.get("description"))}
    return {"available": True, "has_profile": False, "link_count": 0, "types": [],
            "has_description": False}
