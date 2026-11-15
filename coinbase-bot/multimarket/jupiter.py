"""Jupiter quote + price-impact via the free lite API (no key, no swaps).

Only quotes/simulation — this module can never send a swap, has no signer and
touches no key. Returns buy and sell quotes so a round-trip's realistic cost
(price impact + implied slippage) can be checked before any paper decision.
"""

from __future__ import annotations

from typing import Optional

from .discovery import safe_get_json

LITE_QUOTE = "https://lite-api.jup.ag/swap/v1/quote"
WSOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def quote(
    input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50
) -> Optional[dict]:
    """Raw Jupiter quote. `amount` is in the input mint's smallest unit.
    Returns the parsed quote or None (no route / network error)."""
    url = (
        f"{LITE_QUOTE}?inputMint={input_mint}&outputMint={output_mint}"
        f"&amount={amount}&slippageBps={slippage_bps}"
    )
    data = safe_get_json(url)
    if not isinstance(data, dict) or "outAmount" not in data:
        return None
    return data


def alive() -> bool:
    """True if the Jupiter quote API answers for a known liquid pair."""
    return quote(WSOL, USDC, 10_000_000) is not None


def _num(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def round_trip_quote(token_mint: str, usdc_units: int = 10_000_000) -> dict:
    """Buy token with USDC, then quote selling the received amount back.
    Reports price impact both ways and whether a route exists at all
    (a missing sell route is an exit-liquidity red flag)."""
    buy = quote(USDC, token_mint, usdc_units)
    result = {
        "buy_route": buy is not None,
        "sell_route": None,
        "buy_price_impact_pct": None,
        "sell_price_impact_pct": None,
        "sellable": None,
    }
    if buy is None:
        result["sellable"] = None
        return result
    result["buy_price_impact_pct"] = _num(buy.get("priceImpactPct"))
    received = int(buy.get("outAmount", "0"))
    if received <= 0:
        result["sellable"] = False
        return result
    sell = quote(token_mint, USDC, received)
    result["sell_route"] = sell is not None
    if sell is not None:
        result["sell_price_impact_pct"] = _num(sell.get("priceImpactPct"))
        result["sellable"] = True
    else:
        result["sellable"] = False
    return result
