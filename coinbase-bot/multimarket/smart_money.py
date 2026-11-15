"""Smart Money Analyst (workstation 06) — structural read on free endpoints.

What is real here:
  * mint / freeze authority state (an active mint authority means supply can
    still be inflated under holders),
  * Token-2022 program use,
  * the measured on-chain activity rate from the Whale Tracker.

Verified limitations, reported as unavailable rather than estimated:
  * early-buyer detection and per-wallet profit history need a paid indexer,
  * holder concentration needs getTokenLargestAccounts, which the free public
    node refuses.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from .solana_rpc import PUBLIC_RPC, fetch_onchain
from .whale import UNAVAILABLE, analyse as whale_analyse


@dataclass
class SmartMoneyReport:
    mint: str
    mint_authority_active: Optional[bool]
    freeze_authority_active: Optional[bool]
    token_2022: Optional[bool]
    activity: str
    tx_per_hour: Optional[float]
    structural_risk: str            # LOW | MEDIUM | HIGH | UNKNOWN
    holder_concentration: str       # UNAVAILABLE_FREE_RPC
    early_buyer_analysis: str       # UNAVAILABLE_PAID_INDEXER
    profitable_wallet_patterns: str # UNAVAILABLE_PAID_INDEXER
    notes: list

    def to_dict(self) -> dict:
        return asdict(self)


def analyse(mint: str, endpoint: str = PUBLIC_RPC) -> SmartMoneyReport:
    whale = whale_analyse(mint, endpoint)
    oc = fetch_onchain(mint, endpoint)

    known = [v for v in (oc.mint_authority_active, oc.freeze_authority_active) if v is not None]
    if not known:
        risk = "UNKNOWN"
    elif oc.mint_authority_active or oc.freeze_authority_active:
        risk = "HIGH"
    elif whale.activity == "QUIET":
        risk = "MEDIUM"
    else:
        risk = "LOW"

    notes = list(whale.notes)
    notes.append("Early-Buyer- und Gewinnmuster brauchen einen kostenpflichtigen Indexer.")
    return SmartMoneyReport(
        mint=mint,
        mint_authority_active=oc.mint_authority_active,
        freeze_authority_active=oc.freeze_authority_active,
        token_2022=oc.token2022_transfer_fee,
        activity=whale.activity,
        tx_per_hour=whale.tx_per_hour,
        structural_risk=risk,
        holder_concentration=UNAVAILABLE,
        early_buyer_analysis="UNAVAILABLE_PAID_INDEXER",
        profitable_wallet_patterns="UNAVAILABLE_PAID_INDEXER",
        notes=notes,
    )
