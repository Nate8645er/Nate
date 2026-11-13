"""Whale Tracker (workstation 05) — real data from the free Solana RPC.

Measured against the live chain:
  * token supply (getTokenSupply),
  * recent on-chain activity: how many signatures the mint saw in the last
    page, and the time span they cover -> a real transactions-per-hour rate,
  * whether activity is bursty (many tx in a short window).

Verified limitation: `getTokenLargestAccounts` is refused by the public node
("Too many requests for a specific RPC call") for both large and small mints,
so top-holder concentration is reported as UNAVAILABLE_FREE_RPC — never
guessed. A dedicated RPC (own key) would unlock it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from .solana_rpc import PUBLIC_RPC, rpc_call

UNAVAILABLE = "UNAVAILABLE_FREE_RPC"


@dataclass
class WhaleReport:
    mint: str
    supply: Optional[float]
    recent_tx_count: Optional[int]
    window_hours: Optional[float]
    tx_per_hour: Optional[float]
    activity: str                 # QUIET | NORMAL | BURST | UNKNOWN
    top_holder_pct: str           # UNAVAILABLE_FREE_RPC
    concentration: str            # UNAVAILABLE_FREE_RPC
    notes: list

    def to_dict(self) -> dict:
        return asdict(self)


def analyse(mint: str, endpoint: str = PUBLIC_RPC, signature_limit: int = 100) -> WhaleReport:
    notes: list = []

    supply = None
    res = rpc_call("getTokenSupply", [mint], endpoint)
    if isinstance(res, dict):
        supply = (res.get("value") or {}).get("uiAmount")
    if supply is None:
        notes.append("Supply nicht abrufbar")

    sigs = rpc_call("getSignaturesForAddress", [mint, {"limit": signature_limit}], endpoint)
    count = window = rate = None
    activity = "UNKNOWN"
    if isinstance(sigs, list) and sigs:
        count = len(sigs)
        times = [s.get("blockTime") for s in sigs if s.get("blockTime")]
        if len(times) >= 2:
            window = (max(times) - min(times)) / 3600
            rate = (count / window) if window > 0 else None
        if rate is not None:
            activity = "BURST" if rate >= 60 else "NORMAL" if rate >= 1 else "QUIET"
    else:
        notes.append("Signaturen nicht abrufbar")

    notes.append("Top-Holder-Verteilung: getTokenLargestAccounts wird vom freien "
                 "oeffentlichen Node abgelehnt (429 pro Methode). Kein Schaetzwert.")
    notes.append("Wallet-Identitaeten werden nicht behauptet.")
    return WhaleReport(mint, supply, count, window, rate, activity,
                       UNAVAILABLE, UNAVAILABLE, notes)
