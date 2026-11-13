"""HyperGrok capital and risk configuration (Phase 5).

The user set an ABSOLUTE capital ceiling of 17.10 USDC. This value is stored
here and fed into RiskConfig. Live trading stays OFF: limits_confirmed is
False, so no real order can be sent regardless of this number. The ceiling is
never raised automatically by new deposits — it is a hard constant here.
"""

from decimal import Decimal as D

from .core import RiskConfig

# User-set absolute capital ceiling. Must never be exceeded.
CAPITAL_LIMIT_USDC = D("17.10")


def paper_risk_config() -> RiskConfig:
    """Risk config for paper training. Live remains disabled."""
    return RiskConfig(
        allocated_capital_usdc=CAPITAL_LIMIT_USDC,
        absolute_max_loss_usdc=CAPITAL_LIMIT_USDC,  # cannot lose more than the ceiling
        limits_confirmed=False,  # LIVE OFF — only a separate explicit user step flips this
        max_position_fraction=D(
            "1.0"
        ),  # positions up to 100% of capital may be prepared
        daily_loss_limit_usdc=D(
            "2.00"
        ),  # RiskManager tightens; never raises the absolute
        per_trade_risk_usdc=D("1.00"),
        taker_fee_rate=D("0.001"),
        min_order_usdc=D("1"),
    )
