"""Multi-market extension (Phase 8) for the HyperGrok trading team.

Adds token discovery, market-cap categorisation, memecoin risk analysis, a
liquidity-aware micro-cap paper broker, adapter status tracking and virtual
portfolios — all on top of the existing trading_team package, without a second
live engine. Everything is read-only or paper; real execution stays disabled.
"""

from .core import (
    ADAPTERS,
    AdapterStatus,
    MarketCapCategory,
    MicroCapPaperBroker,
    Portfolio,
    RiskReport,
    Token,
    assess_memecoin_risk,
    categorize_market_cap,
    should_veto,
    valuation,
)
from .discovery import DexScreenerSource, GeckoTerminalSource, TokenScanner

__all__ = [
    "ADAPTERS",
    "AdapterStatus",
    "MarketCapCategory",
    "MicroCapPaperBroker",
    "Portfolio",
    "RiskReport",
    "Token",
    "assess_memecoin_risk",
    "categorize_market_cap",
    "should_veto",
    "valuation",
    "DexScreenerSource",
    "GeckoTerminalSource",
    "TokenScanner",
]
