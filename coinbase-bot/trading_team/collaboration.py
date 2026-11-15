"""Collaborative decision room (Phase 2).

All voices see the SAME market data and argue a stance. No rigid single-role
pipeline: each voice may analyse, propose, and challenge the others. The
RiskManager keeps its binding veto — a consensus to BUY still has to pass
risk evaluation, and the room readily returns NO TRADE.

This orchestrates the EXISTING agents; it is not a second trading engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal as D
from typing import Callable, Literal

from . import indicators as ind
from .core import AnalystReport, RiskManager, Signal

Stance = Literal["BUY", "SELL", "HOLD"]


@dataclass(frozen=True)
class Opinion:
    voice: str
    stance: Stance
    confidence: D  # 0..1
    rationale: str


@dataclass(frozen=True)
class Consensus:
    stance: Stance
    confidence: D
    agreed: bool
    opinions: list[Opinion]
    challenges: list[str]


# Each voice: name + function(report, closes) -> Opinion
Voice = Callable[[AnalystReport, list], Opinion]


def trend_voice(report: AnalystReport, closes: list) -> Opinion:
    if report.trend == "up":
        return Opinion("Trend", "BUY", D("0.7"), "SMA-fast über SMA-slow")
    if report.trend == "down":
        return Opinion("Trend", "SELL", D("0.7"), "SMA-fast unter SMA-slow")
    return Opinion("Trend", "HOLD", D("0.4"), "Seitwärts")


def momentum_voice(report: AnalystReport, closes: list) -> Opinion:
    try:
        r = ind.rsi(closes)
    except ValueError:
        return Opinion("Momentum", "HOLD", D("0.3"), "zu wenig Daten")
    if r < 30:
        return Opinion("Momentum", "BUY", D("0.6"), f"RSI {r:.0f} überverkauft")
    if r > 70:
        return Opinion("Momentum", "SELL", D("0.6"), f"RSI {r:.0f} überkauft")
    if report.momentum > D("0.002"):
        return Opinion("Momentum", "BUY", D("0.5"), f"RSI {r:.0f}, positives Momentum")
    return Opinion("Momentum", "HOLD", D("0.4"), f"RSI {r:.0f} neutral")


def mean_reversion_voice(report: AnalystReport, closes: list) -> Opinion:
    try:
        b = ind.bollinger(closes)
    except ValueError:
        return Opinion("MeanReversion", "HOLD", D("0.3"), "zu wenig Daten")
    price = float(report.last_price)
    if price <= b["lower"]:
        return Opinion(
            "MeanReversion", "BUY", D("0.55"), "Preis am unteren Bollinger-Band"
        )
    if price >= b["upper"]:
        return Opinion(
            "MeanReversion", "SELL", D("0.55"), "Preis am oberen Bollinger-Band"
        )
    return Opinion("MeanReversion", "HOLD", D("0.4"), "innerhalb der Bänder")


def volatility_skeptic_voice(report: AnalystReport, closes: list) -> Opinion:
    # High volatility -> argue against taking new risk.
    if report.volatility > D("0.03"):
        return Opinion(
            "VolSkeptiker",
            "HOLD",
            D("0.6"),
            f"hohe Volatilität {report.volatility:.3f}, Risiko gegen Einstieg",
        )
    return Opinion("VolSkeptiker", "HOLD", D("0.3"), "Volatilität vertretbar")


DEFAULT_VOICES: list[Voice] = [
    trend_voice,
    momentum_voice,
    mean_reversion_voice,
    volatility_skeptic_voice,
]


class DebateRoom:
    def __init__(self, voices: list[Voice] | None = None):
        self.voices = voices or DEFAULT_VOICES

    def deliberate(self, report: AnalystReport, closes: list) -> Consensus:
        opinions = [v(report, closes) for v in self.voices]
        score: dict[Stance, D] = {"BUY": D("0"), "SELL": D("0"), "HOLD": D("0")}
        for o in opinions:
            score[o.stance] += o.confidence
        winner = max(score, key=lambda s: score[s])
        total = sum(score.values()) or D("1")
        confidence = score[winner] / total
        challenges = [
            f"{o.voice} widerspricht ({o.stance}): {o.rationale}"
            for o in opinions
            if o.stance != winner
        ]
        votes_for = sum(1 for o in opinions if o.stance == winner)
        agreed = votes_for * 2 > len(opinions)
        return Consensus(winner, confidence, agreed, opinions, challenges)


def consensus_to_signal(
    consensus: Consensus,
    report: AnalystReport,
    stop_pct: D = D("0.02"),
    take_pct: D = D("0.04"),
    base_fraction: D = D("0.5"),
) -> Signal:
    """Turn a BUY consensus into a sized signal. Anything else is NO TRADE/flat
    or a SELL to close."""
    price = report.last_price
    if consensus.stance == "BUY" and consensus.agreed:
        frac = min(base_fraction * consensus.confidence * 2, D("1.0"))
        return Signal(
            report.symbol,
            "BUY",
            f"Konsens BUY (Konfidenz {consensus.confidence:.2f})",
            entry=price,
            stop_loss=price * (1 - stop_pct),
            take_profit=price * (1 + take_pct),
            size_fraction=frac,
        )
    if consensus.stance == "SELL":
        return Signal(report.symbol, "SELL", "Konsens SELL / schließen", entry=price)
    return Signal(
        report.symbol,
        None,
        f"NO TRADE (Konsens {consensus.stance}, " f"agreed={consensus.agreed})",
    )


def collaborative_cycle(
    symbol: str, closes: list, analyst, risk: RiskManager, room: DebateRoom
) -> dict:
    """One collaborative decision: debate -> signal -> binding risk check.
    Returns a transparent record; places no order."""
    report = analyst.analyse(symbol, closes)
    consensus = room.deliberate(report, closes)
    signal = consensus_to_signal(consensus, report)
    record = {
        "symbol": symbol,
        "opinions": [
            (o.voice, o.stance, str(o.confidence)) for o in consensus.opinions
        ],
        "consensus": consensus.stance,
        "agreed": consensus.agreed,
        "challenges": consensus.challenges,
        "signal": signal.side,
    }
    if signal.side == "BUY":
        decision = risk.evaluate(signal)
        record["risk_approved"] = decision.approved
        record["risk_reason"] = decision.reason
        record["decision"] = "prepare_buy" if decision.approved else "rejected_by_risk"
    elif signal.side == "SELL":
        record["decision"] = "prepare_sell"
    else:
        record["decision"] = "no_trade"
    return record
