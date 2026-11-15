"""HyperGrok autonomous trading team (Phase 4).

Built on the verified Coinbase live connector. Real-money execution stays
disabled: the team runs in paper mode until a human confirms an absolute
capital and loss limit, and even then every real order passes through the
connector's existing approval guards.
"""

from . import backtest, indicators
from .collaboration import (
    Consensus,
    DebateRoom,
    Opinion,
    collaborative_cycle,
    consensus_to_signal,
)
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
from .hypergrok_config import CAPITAL_LIMIT_USDC, paper_risk_config

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
    "backtest",
    "indicators",
    "Consensus",
    "DebateRoom",
    "Opinion",
    "collaborative_cycle",
    "consensus_to_signal",
    "CAPITAL_LIMIT_USDC",
    "paper_risk_config",
]
