"""HyperGrok autonomous trading team (Phase 4).

Built on the verified Coinbase live connector. Real-money execution stays
disabled: the team runs in paper mode until a human confirms an absolute
capital and loss limit, and even then every real order passes through the
connector's existing approval guards.
"""

from .core import (
    AnalystReport,
    ExecutionAgent,
    MarketAnalyst,
    PaperBroker,
    RiskConfig,
    RiskDecision,
    RiskManager,
    Signal,
    Strategist,
    Supervisor,
    TradeReviewer,
)

__all__ = [
    "AnalystReport",
    "ExecutionAgent",
    "MarketAnalyst",
    "PaperBroker",
    "RiskConfig",
    "RiskDecision",
    "RiskManager",
    "Signal",
    "Strategist",
    "Supervisor",
    "TradeReviewer",
]
