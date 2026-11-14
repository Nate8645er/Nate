"""Nate's confirmed live risk configuration (Phase 14).

This is the single source of truth for the ceilings. Agents read it, the
RiskManager may tighten it, and nothing in the codebase may raise it.

Confirmed by Nate on 2026-11-13:

    Exchange                Coinbase Advanced Trade
    Market                  SPOT only
    MAX_ALLOCATED_CAPITAL   17.10 USDC
    MAX_POSITION_FRACTION   1.0   (one position may use the whole allocation)
    MAX_DAILY_LOSS          17.10 USDC
    MAX_TOTAL_LOSS          17.10 USDC
    MAX_SLIPPAGE            2.0 %
    LEVERAGE / MARGIN       disabled
    WITHDRAWALS / TRANSFERS disabled

Two things about this configuration are stated plainly rather than hidden:

  1. MAX_DAILY_LOSS and MAX_TOTAL_LOSS both equal the full allocation, so no
     loss ceiling engages before the entire 17.10 USDC is gone. The
     configuration permits a total loss of the allocated capital. That is
     Nate's explicit choice; it is implemented exactly as given.
  2. MAX_SLIPPAGE 2.0 % is LOOSER than the 1.0 % placeholder that
     ``AbsoluteLimits`` carried as a default before this phase. It is set here
     by direct instruction, as part of the one confirmed baseline, and it is
     the only value in this file that is less strict than the old placeholder.
     After this baseline is installed, nothing may raise it again.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal as D

from .core import RiskConfig
from .modes import AbsoluteLimits

CONFIRMED_ON = "2026-11-13"
CONFIRMED_BY = "Nate"

EXCHANGE = "Coinbase Advanced Trade"
MARKET = "SPOT"

MAX_ALLOCATED_CAPITAL_USDC = D("17.10")
MAX_POSITION_FRACTION = D("1.0")
MAX_DAILY_LOSS_USDC = D("17.10")
MAX_TOTAL_LOSS_USDC = D("17.10")
MAX_SLIPPAGE_PCT = D("2.0")

LEVERAGE_ENABLED = False
MARGIN_ENABLED = False
WITHDRAWALS_ENABLED = False
TRANSFERS_ENABLED = False

#: Products this configuration permits. Spot pairs quoted in USDC only.
ALLOWED_PRODUCTS = ("BTC-USDC", "ETH-USDC", "SOL-USDC")


@dataclass(frozen=True)
class RiskProfile:
    """The confirmed configuration in one object, for reports and checks."""

    exchange: str = EXCHANGE
    market: str = MARKET
    max_allocated_capital_usdc: D = MAX_ALLOCATED_CAPITAL_USDC
    max_position_fraction: D = MAX_POSITION_FRACTION
    max_daily_loss_usdc: D = MAX_DAILY_LOSS_USDC
    max_total_loss_usdc: D = MAX_TOTAL_LOSS_USDC
    max_slippage_pct: D = MAX_SLIPPAGE_PCT
    leverage_enabled: bool = LEVERAGE_ENABLED
    margin_enabled: bool = MARGIN_ENABLED
    withdrawals_enabled: bool = WITHDRAWALS_ENABLED
    transfers_enabled: bool = TRANSFERS_ENABLED
    confirmed_on: str = CONFIRMED_ON
    confirmed_by: str = CONFIRMED_BY

    def max_position_usdc(self) -> D:
        return self.max_allocated_capital_usdc * self.max_position_fraction

    def permits_total_loss(self) -> bool:
        """True when no loss ceiling engages before the allocation is gone."""
        return (
            self.max_total_loss_usdc >= self.max_allocated_capital_usdc
            and self.max_daily_loss_usdc >= self.max_allocated_capital_usdc
        )

    def to_dict(self) -> dict:
        return {
            "exchange": self.exchange,
            "market": self.market,
            "max_allocated_capital_usdc": str(self.max_allocated_capital_usdc),
            "max_position_fraction": str(self.max_position_fraction),
            "max_position_usdc": str(self.max_position_usdc()),
            "max_daily_loss_usdc": str(self.max_daily_loss_usdc),
            "max_total_loss_usdc": str(self.max_total_loss_usdc),
            "max_slippage_pct": str(self.max_slippage_pct),
            "leverage_enabled": self.leverage_enabled,
            "margin_enabled": self.margin_enabled,
            "withdrawals_enabled": self.withdrawals_enabled,
            "transfers_enabled": self.transfers_enabled,
            "allowed_products": list(ALLOWED_PRODUCTS),
            "permits_total_loss_of_allocation": self.permits_total_loss(),
            "confirmed_by": self.confirmed_by,
            "confirmed_on": self.confirmed_on,
        }


NATE_PROFILE = RiskProfile()

#: The confirmed ceilings as the ``AbsoluteLimits`` the ModeController takes.
#: ``confirmed=True`` records that a human stated these values explicitly; it
#: does NOT by itself unlock autonomous live trading (see modes.py).
NATE_CONFIRMED_LIMITS = AbsoluteLimits(
    total_capital_usdc=MAX_ALLOCATED_CAPITAL_USDC,
    max_daily_loss_usdc=MAX_DAILY_LOSS_USDC,
    max_total_loss_usdc=MAX_TOTAL_LOSS_USDC,
    max_slippage_pct=MAX_SLIPPAGE_PCT,
    max_open_exposure_usdc=MAX_ALLOCATED_CAPITAL_USDC * MAX_POSITION_FRACTION,
    confirmed=True,
)


#: Read by the readiness report. Stays False: arming happens only through
#: ModeController.arm_autonomous with Nate's activation phrase.
LIVE_AUTONOMOUS_ENABLED = False


def live_risk_config(taker_fee_rate: D = D("0.001"), min_order_usdc: D = D("1")) -> RiskConfig:
    """The RiskManager's view of the same confirmed values."""
    return RiskConfig(
        allocated_capital_usdc=MAX_ALLOCATED_CAPITAL_USDC,
        absolute_max_loss_usdc=MAX_TOTAL_LOSS_USDC,
        limits_confirmed=True,
        max_position_fraction=MAX_POSITION_FRACTION,
        daily_loss_limit_usdc=MAX_DAILY_LOSS_USDC,
        taker_fee_rate=taker_fee_rate,
        min_order_usdc=min_order_usdc,
    )
