"""The 15 visible workstations and how each maps to real backend capability.

Honesty rule: a workstation is only "connected" when a real function in this
repository drives it. Everything else reports NOT_CONNECTED, so the office
never pretends to run fifteen independent AI processes.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Workstation:
    id: str
    num: int
    name: str
    short: str
    color: str
    backend: str       # module/function that really drives it, or ""
    connected: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = "IDLE" if self.connected else "NOT CONNECTED"
        return d


W = Workstation
WORKSTATIONS = [
    W("ceo", 1, "CEO / Orchestrator", "CEO", "#ffd34d",
      "trading_team.meeting.hold_meeting (Supervisor-Rolle)", True),
    W("market", 2, "Crypto Market Analyst", "CMA", "#4b8cff",
      "trading_team.core.MarketAnalyst", True),
    W("pumpfun", 3, "Pump.fun Scanner", "PFS", "#2ff39a",
      "multimarket.discovery (GeckoTerminal/DexScreener Pools)", True),
    W("meme", 4, "Memecoin Hunter", "MH", "#ff5577",
      "multimarket.discovery.TokenScanner", True),
    W("whale", 5, "Whale Tracker", "WT", "#9d6bff",
      "multimarket.whale.analyse (Solana RPC: Supply + Aktivitaetsrate)", True),
    W("smart", 6, "Smart Money Analyst", "SMA", "#22e8ff",
      "multimarket.smart_money.analyse (Authority-Struktur + Aktivitaet)", True),
    W("ta", 7, "Technical Analysis", "TA", "#ff6bd6",
      "trading_team.indicators (RSI/MACD/ATR/Bollinger)", True),
    W("social", 8, "Social / Attention", "SS", "#ff9f43",
      "multimarket.social.trending_assets (CoinGecko Trending; kein Sentiment-Score)", True),
    W("onchain", 9, "On-Chain Intelligence", "OCI", "#4bb8ff",
      "multimarket.solana_rpc.fetch_onchain", True),
    W("rug", 10, "Rug Pull & Scam Detector", "RSD", "#c6ff4d",
      "multimarket.core.assess_memecoin_risk", True),
    W("strategy", 11, "AI Strategy", "ATS", "#a78bfa",
      "trading_team.collaboration.DebateRoom + strategies", True),
    W("risk", 12, "Risk Manager", "RM", "#34d399",
      "trading_team.core.RiskManager (Veto)", True),
    W("exec", 13, "Trading Execution", "TE", "#fb7185",
      "coinbase_connector + trading_team.modes (Gate)", True),
    W("portfolio", 14, "Portfolio Manager", "PM", "#60a5fa",
      "multimarket.core.Portfolio", True),
    W("learn", 15, "Learning & Optimization", "L&O", "#f472b6",
      "trading_team.backtest (Walk-Forward/Overfitting)", True),
]

# Which workstation each meeting agent lights up.
AGENT_TO_STATION = {
    "MarketAnalyst": "market",
    "Strategist": "strategy",
    "RiskManager": "risk",
    "ExecutionAgent": "exec",
    "TradeReviewer": "portfolio",
    "Supervisor": "ceo",
    "Gate": "exec",
    "Trend": "ta",
    "Momentum": "ta",
    "MeanReversion": "strategy",
    "VolSkeptiker": "risk",
}


def stations() -> list:
    return [w.to_dict() for w in WORKSTATIONS]


def connected_count() -> tuple:
    c = sum(1 for w in WORKSTATIONS if w.connected)
    return c, len(WORKSTATIONS)
