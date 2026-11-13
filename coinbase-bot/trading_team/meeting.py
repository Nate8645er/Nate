"""The AI team meeting that must happen before every trade (Phase 10).

Eight steps, each producing a recorded statement from a named agent, so every
decision is traceable:

  1 MarketAnalyst   analyses current market data
  2 Strategist      proposes a trading plan
  3 Debate room     all voices argue on the SAME data and may disagree
  4 RiskManager     evaluates risk  -> may VETO (binding)
  5 Supervisor      checks the consensus
  6 ExecutionAgent  prepares the order (never sends it here)
  7 TradeReviewer   checks the prepared order against the limits
  8 Gate            execution only if the mode allows AND approval matches

There is never an obligation to trade: any step may end the meeting with
NO_TRADE, and a RiskManager VETO blocks every new order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal as D
from enum import Enum
from typing import Optional

from .collaboration import DebateRoom, consensus_to_signal
from .core import MarketAnalyst, RiskManager
from .modes import ModeController, TradingMode


class Decision(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_TRADE = "NO TRADE"
    VETO = "VETO"


@dataclass(frozen=True)
class Statement:
    step: int
    agent: str
    decision: Decision
    rationale: str
    data: dict = field(default_factory=dict)


@dataclass
class MeetingResult:
    symbol: str
    started_at: str
    statements: list = field(default_factory=list)
    consensus: Optional[str] = None
    agreed: bool = False
    challenges: list = field(default_factory=list)
    prepared_order: Optional[dict] = None
    final: Decision = Decision.NO_TRADE
    executed: bool = False
    execution_note: str = ""

    def say(self, step: int, agent: str, decision: Decision, rationale: str, data: dict = None) -> None:
        self.statements.append(Statement(step, agent, decision, rationale, data or {}))

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "started_at": self.started_at,
            "statements": [
                {"step": s.step, "agent": s.agent, "decision": s.decision.value,
                 "rationale": s.rationale, "data": s.data}
                for s in self.statements
            ],
            "consensus": self.consensus,
            "agreed": self.agreed,
            "challenges": self.challenges,
            "prepared_order": self.prepared_order,
            "final": self.final.value,
            "executed": self.executed,
            "execution_note": self.execution_note,
        }


def hold_meeting(symbol: str, closes: list, *, risk: RiskManager,
                 controller: ModeController, available_usdc: D,
                 open_exposure_usdc: D = D("0"), approval: Optional[str] = None,
                 analyst: Optional[MarketAnalyst] = None,
                 room: Optional[DebateRoom] = None,
                 fee_rate: D = D("0.001"), min_order_usdc: D = D("1")) -> MeetingResult:
    """Run the full eight-step meeting. Sends no order itself: step 8 only
    reports whether the gate would open, and for whom."""
    analyst = analyst or MarketAnalyst()
    room = room or DebateRoom()
    result = MeetingResult(symbol=symbol, started_at=datetime.now(timezone.utc).isoformat())

    # Step 1 - MarketAnalyst
    report = analyst.analyse(symbol, closes)
    result.say(1, "MarketAnalyst", Decision.HOLD,
               f"Trend {report.trend}, Momentum {report.momentum:.4f}, Vol {report.volatility:.4f}",
               {"price": str(report.last_price), "trend": report.trend})

    # Step 2 - Strategist (via the debate room's consensus signal)
    consensus = room.deliberate(report, closes)
    result.consensus, result.agreed = consensus.stance, consensus.agreed
    result.challenges = list(consensus.challenges)
    signal = consensus_to_signal(consensus, report)
    plan_decision = {"BUY": Decision.BUY, "SELL": Decision.SELL}.get(signal.side or "", Decision.NO_TRADE)
    result.say(2, "Strategist", plan_decision, signal.reason,
               {"stop_loss": str(signal.stop_loss), "take_profit": str(signal.take_profit)})

    # Step 3 - the whole team argues on the same data
    for opinion in consensus.opinions:
        stance = {"BUY": Decision.BUY, "SELL": Decision.SELL}.get(opinion.stance, Decision.HOLD)
        result.say(3, opinion.voice, stance, opinion.rationale,
                   {"confidence": str(opinion.confidence)})

    if signal.side is None:
        result.say(4, "RiskManager", Decision.NO_TRADE, "Kein Handelsplan zu bewerten")
        result.final = Decision.NO_TRADE
        return result

    # Step 4 - RiskManager, binding
    decision = risk.evaluate(signal)
    if not decision.approved:
        result.say(4, "RiskManager", Decision.VETO, decision.reason)
        result.final = Decision.VETO
        result.say(5, "Supervisor", Decision.NO_TRADE, "Veto des RiskManagers ist bindend")
        return result
    result.say(4, "RiskManager", plan_decision, decision.reason,
               {"quote_size": str(decision.quote_size_usdc)})

    # Step 5 - Supervisor checks the consensus
    if not consensus.agreed:
        result.say(5, "Supervisor", Decision.NO_TRADE,
                   f"Kein belastbarer Konsens ({len(consensus.challenges)} Gegenstimmen)")
        result.final = Decision.NO_TRADE
        return result
    result.say(5, "Supervisor", plan_decision, "Konsens getragen, Meeting darf fortfahren")

    # Step 6 - ExecutionAgent prepares, sized against the REAL balance
    cap = controller.max_position_usdc(available_usdc, open_exposure_usdc)
    size = min(decision.quote_size_usdc, cap).quantize(D("0.01"), rounding=ROUND_DOWN)
    fee = (size * fee_rate).quantize(D("0.0001"))
    if size < min_order_usdc:
        result.say(6, "ExecutionAgent", Decision.NO_TRADE,
                   f"Ordergroesse {size} unter Minimum {min_order_usdc}")
        result.final = Decision.NO_TRADE
        return result
    order = {"side": signal.side, "product_id": symbol, "quote_size": str(size),
             "est_fee_usdc": str(fee), "stop_loss": str(signal.stop_loss),
             "take_profit": str(signal.take_profit),
             "approval_phrase": controller.approval_phrase(signal.side, symbol, str(size))}
    result.prepared_order = order
    result.say(6, "ExecutionAgent", plan_decision,
               f"Order vorbereitet: {size} USDC (Deckel {cap}), Gebuehr ca. {fee}", order)

    # Step 7 - TradeReviewer checks the prepared order against the ceilings
    problems = []
    if size > controller.limits.total_capital_usdc:
        problems.append("ueber Kapitalgrenze")
    if size > available_usdc:
        problems.append("ueber verfuegbarem Guthaben")
    if problems:
        result.say(7, "TradeReviewer", Decision.VETO, "; ".join(problems))
        result.final = Decision.VETO
        return result
    result.say(7, "TradeReviewer", plan_decision,
               "Groesse, Gebuehr und Limits konsistent; Entscheidung nachvollziehbar")

    # Step 8 - the gate. Nothing is sent from inside the meeting.
    allowed, reason = controller.may_execute_live(signal.side, symbol, str(size), approval)
    result.final = plan_decision
    result.executed = False
    if controller.mode is TradingMode.PAPER:
        result.execution_note = "PAPER: Order nur simuliert, keine echte Ausfuehrung."
    elif allowed:
        result.execution_note = f"{reason} - Order darf jetzt ueber den Connector gesendet werden."
    else:
        result.execution_note = f"Gesperrt: {reason}"
    result.say(8, "Gate", plan_decision if allowed else Decision.NO_TRADE, result.execution_note)
    return result
